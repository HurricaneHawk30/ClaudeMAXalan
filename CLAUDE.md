# tutor bot programming cycle

Name used by the user for this whole recipe: **"tutor bot programming cycle"**.
When they mention it, follow everything below (also available as the skill
`/tutor-bot-programming-cycle`).

## 1. What this is
One engine, `tutor/`, runs ONE Telegram bot (standard library only, Python 3.10+). Every subject is a
module inside it (`tutor/subjects/`). A request like "a bot for subject X" means adding a module to
this engine, not creating a new bot. A separate bot with its own token (`BOT=<name>`) is made only if
Alan explicitly asks for it. The architecture contract is `docs/ARCHITECTURE.md`; if code and document
disagree, the document wins.

## 2. Run
| Variable | Meaning |
|---|---|
| `TELEGRAM_BOT_TOKEN` | bot token from @BotFather (with `BOT=<name>`: `TELEGRAM_BOT_TOKEN_<NAME>`) |
| `TUTOR_OWNER_ID` | Telegram user id of the owner (owner commands, safety alerts) |
| `ANTHROPIC_API_KEY` | optional; without it the bot is fully deterministic and costs nothing |
| `TUTOR_MODEL` | LLM model id (default `claude-haiku-5-5`) |
| `TUTOR_DB` | SQLite path (default `data/tutor.db`, or `data/tutor-<bot>.db` when `BOT` is set) |
| `TUTOR_LLM_DAILY_LIMIT` | LLM calls per student per day (default 40) |
| `TUTOR_LLM_GLOBAL_DAILY_LIMIT` | LLM calls per day for all students together (default 1000) |

Put them in `.env` (gitignored, never commit) or the environment. The cloud environment must allow
`api.telegram.org` (and `api.anthropic.com` if the LLM is used).
- `python3 -m tutor --check` checks the token (and the LLM).
- `python3 -m tutor` runs the bot (long polling; it restarts itself after unexpected errors). Only ONE
  getUpdates consumer per token.
- Do NOT write anything to the user in the Claude chat about bot activity; speak only when asked.

## 3. Codes
Access codes are secret and ONE-TIME (8 characters from `ABCDEFGHJKMNPQRSTUVWXYZ23456789`: no 0/O, 1/I/L). When Alan
says "дай N кодов", run `python3 -m tutor codes N` and show the codes ONLY in the Claude chat.
"Block / reset a user" = owner command `/reset CHAT_ID`; the student then needs a new code.
After 10 wrong codes from one chat within an hour the owner gets one alert (at most one per hour).

## 4. Owner commands (only from `TUTOR_OWNER_ID`)
`/codes N` (1-50), `/students`, `/student CHAT_ID`, `/reset CHAT_ID`, `/flags`, `/flags done [N]`, `/stats`.
`/flags` only LISTS new safety flags; after dealing with them send `/flags done N` (N = the last id listed;
plain `/flags done` marks all). Students can send `/delete_my_data` to erase everything stored about them,
except unreviewed safety flags: those stay until the owner has reviewed them, then they are deleted too.

## 5. Adding a subject
Add one file `tutor/subjects/<name>.py` with `def register(reg): reg.register(Subject(...), [Skill(...), ...])`,
or a JSON question bank (`tutor/content/bank.py`). The property tests cover new skills automatically.
Spot-check generated problems with `python3 -m tutor sample SKILL_ID [LEVEL] [N]`.

## 6. Tests
**ALWAYS run `python3 -m unittest discover -s tests` before any update or deploy, and never ship red.**
The default run takes under a minute (60 seeds per generated skill). Before every deploy ALSO run the full
property test: `TUTOR_FULL_TESTS=1 python3 -m unittest discover -s tests` (300 seeds, about 2 minutes).

## 7. Rules
- Correctness is decided by code (the checker), never by the LLM; the LLM only phrases hints and feedback.
- Plain text only (no Markdown/LaTeX); bot language is English; one problem per message, numbered.
- Safety: distress messages get the fixed DISTRESS text, a flag and an owner alert; the LLM is never called.
  This happens even when the chat is flood-limited. The LLM prompts also tell it to send a student who
  mentions harm, danger, abuse or distress to a trusted adult. Homework/test-answer requests get the CHEAT text.
- Keep the minimum data; never send names or chat ids to the LLM; never log message texts.

## 8. Flow and verbatim texts
Flow: access code -> subject (Year 11 by default) -> topic -> lesson. The year is changed only with
`🎓 Change year`. A VERIFIED student who sends /start is NOT asked for a code: pending is cleared and they
resume at the subject step. An unverified chat gets the code request (keyboard removed).
The legacy button `⚙️ Change year / topic` is still accepted but never sent. Bottom rows of keyboards
carry `🎓 Change year` / `📘 Change subject`. Texts live in `tutor/texts.py`.

```
CODE_REQUEST  = "🔐 Please enter your access code to start the lesson."
CODE_BAD      = "❌ That code isn't valid. Please check it and try again."
CODE_OK       = "✅ Code accepted — welcome! You're all set."
YEAR_ASK      = "🎓 Great! Which year group are you in? Tap the button below (British school system, Year 1–13)."
SUBJECT_ASK    = "📘 Which subject would you like to study? (Year {year}, British curriculum)"
YEAR_NOT_READY = "🚧 Sorry — I don't have lessons for {year_label} yet. Please choose another year group."
TOPIC_ASK     = "📚 What are you working on right now? Here's what students usually study in Year {year} — tap one, or choose «My own topic»."
OWN_TOPIC_ASK = "✍️ Tell me what you'd like to practise and I'll set problems on it."
TOPIC_START   = "🎯 Got it — switching to «{topic}». Let's start with an easy one."
PROBLEM       = "Problem {n}: {text}\n\nSend me your answer (and show your working!) 😊"
PROBLEM_EXAM  = "Problem {n} ({marks} mark{s}): {text}\n\nSend me your answer (and show your working!) 😊"
CORRECT       = "✅ Correct! {solution}."
WRONG         = "❌ Not quite. {why}. Correct answer: {answer}"
HINT          = "💡 Hint: {hint}"
SKIP          = "👀 No problem — here's how to do it: {solution}. Answer: {answer}"
```
Other texts (hints, unparsed, off-topic, cheat, distress, errors, owner texts) are in `tutor/texts.py`.

Keyboards (never send `⚙️ Change year / topic`):
```
Year:     [Year 7 ] [Year 8 ] [Year 9 ]
          [Year 10] [Year 11] [Year 12]
          [Year 13] [Year 1–6]
Subject:  [Maths] [Physics]            (Year 8: [Maths] only)
          [🎓 Change year]
Topic (Year 11 Maths):
          [GCSE Higher: algebra & functions] [GCSE Higher: trig & geometry]
          [GCSE Foundation: number         ] [GCSE Foundation: geometry   ]
          [Past paper practice             ] [My own topic                ]
          [🎓 Change year                  ] [📘 Change subject           ]
```
Years 1-6, 12 and 13 answer YEAR_NOT_READY and keep the previous year. The topic keyboard stays attached
to lesson messages so it is always reachable.

## 9. Legacy `relay/`
`relay/` (Claude answers through a monitor) and `bot.py` are kept, but never run them at the same time as
the engine on the same token: only one getUpdates consumer per bot.
