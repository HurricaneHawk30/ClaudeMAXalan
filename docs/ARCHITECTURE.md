# Tutor Engine v1: architecture and implementation plan

*Target: Python ≥ 3.10 (the environment has 3.13.18), standard library only. This document is the contract between the three agents. If the code and this document disagree, the document wins. If a contract turns out to be impossible, stop and report it rather than changing it quietly.*

## 0. Refinements to the spec (decided here)

1. **Common mistakes are stored as data, not as a `diagnose()` function.** Each problem carries `Problem.mistakes = tuple[Mistake(answer, feedback)]`, so the whole pending problem (text, answer, solution, hint, mistakes) can be saved as JSON in the DB. A restart or a code change cannot change a problem the student has already been shown.
2. **Checker verdicts have four values:** `correct | wrong | unparsed | unmarkable`. Text that is not an answer is never marked wrong. A right value in the wrong form (not in standard form, not factorised, not simplest) counts as `wrong`, with fixed feedback.
3. **Expression equivalence uses fixed pseudo-random points** (listed in §3.3), so tests are deterministic.
4. **`/start` (owner decision, 12 Nov 2026):** an unverified chat gets the code request. An already-verified student is NOT asked for a code again: pending is cleared and they resume at the subject step. Access is revoked only by the owner's `/reset`.
5. **Code alphabet** is `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (no 0/O/1/I/L), 8 characters, using `secrets`. Input is normalised: spaces and hyphens removed, uppercased.
6. **The year is stored only if it has content.** "Year 1–6", 12 and 13 show "not ready" and keep the previous year.
7. **Legacy button** `⚙️ Change year / topic` is still accepted as input and works like `🎓 Change year`. It is never sent.
8. **Default DB path** is `data/tutor.db`. If `BOT=<name>` is set it is `data/tutor-<name>.db`, so two bots never share a getUpdates offset. `TUTOR_ENV_FILE` can override the `.env` path; tests use this.
9. **Extra CLI:** `python3 -m tutor sample SKILL_ID [LEVEL] [N]` prints generated problems so the owner can spot-check them.
10. **The LLM is the only network call inside `Engine.handle`,** and it is injected. With `llm=None` the bot is fully deterministic and costs nothing to run.

## 1. Package layout and ownership (no overlaps)

| Agent | Files |
|---|---|
| **api-dev-core** | `tutor/__init__.py`, `tutor/__main__.py`, `tutor/config.py`, `tutor/messages.py`, `tutor/texts.py`, `tutor/db.py`, `tutor/intents.py`, `tutor/llm.py`, `tutor/owner.py`, `tutor/engine.py`, `tutor/telegram.py`, `CLAUDE.md`, `.claude/skills/tutor-bot-programming-cycle/SKILL.md`, `README.md`, `.gitignore`, `.env.example` |
| **api-dev-content** | `tutor/content/__init__.py`, `tutor/content/base.py`, `tutor/content/mathexpr.py`, `tutor/content/checker.py`, `tutor/content/registry.py`, `tutor/content/bank.py`, `tutor/content/fmt.py` (private helpers), `tutor/subjects/__init__.py`, `tutor/subjects/maths.py`, `tutor/subjects/physics.py` |
| **test-dev** | `tests/__init__.py`, `tests/helpers.py`, `tests/test_mathexpr.py`, `tests/test_checker.py`, `tests/test_skills.py`, `tests/test_registry.py`, `tests/test_bank.py`, `tests/test_flow.py`, `tests/test_lesson.py`, `tests/test_owner.py`, `tests/test_safety.py`, `tests/test_llm.py`, `tests/test_persistence.py`, `tests/test_telegram.py`, `tests/test_config.py`, `tests/test_cli.py`, `tests/fixtures/bank_sample.json`, `tests/fixtures/bank_invalid.json` |

Nobody touches `bot.py` or `relay/`. Core may import from `bot.py` but does not need to.

**Build order**
- **Content** writes `tutor/content/base.py` first, exactly as in §2.1, because core and tests import it. Then: mathexpr → checker → registry → maths → physics → bank.
- **Core** must not create content files. If `base.py` is not there yet, write against the contract and import it later.

**Import rule:** `tutor.content` never imports from `tutor.*` core modules. Core imports only what `tutor.content` exports (§2.6).

---

## 2. Content contracts (api-dev-content implements; core and tests consume)

### 2.1 `tutor/content/base.py` (write exactly)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

PAST_PAPER_LABEL = "Past paper practice"
MY_OWN_TOPIC_LABEL = "My own topic"
ANSWER_KINDS = ("number", "fraction", "set", "assign", "expr", "ratio", "rubric")

@dataclass(frozen=True)
class Answer:
    kind: str                    # one of ANSWER_KINDS
    display: str                 # canonical text shown after "Correct answer: "; check(answer, display) MUST be "correct" (except rubric)
    value: object = None         # number: float (exact, unrounded) | fraction: "p/q" or "p" | set: list[str] of numbers ("2", "-3", "1/2", "2.5")
                                 # assign: dict[str, str] var->number str | expr: str in Python syntax ("x**2+5*x+6") | ratio: list[int] | rubric: None
    dp: int | None = None        # number / set elements: decimal places stated in the question (0..3)
    sf: int | None = None        # number: significant figures stated (>= 2)
    form: str = "any"            # number: any|standard  fraction: any|simplest  expr: any|expanded|factorised  ratio: any|simplest
    ordered: bool = False        # set: order matters (shares of a ratio)
    var: str = "x"               # expr: the single variable letter ("x" or "n")
    mark_scheme: str = ""        # rubric only (display = model answer)
    max_marks: int = 0           # rubric only

@dataclass(frozen=True)
class Mistake:
    answer: Answer               # a typical wrong answer (never equal to the correct one)
    feedback: str                # kind, specific, no trailing period, e.g. "It looks like you found 15% but didn't add it on"

@dataclass(frozen=True)
class Problem:
    skill_id: str
    level: int                   # generator level 1..5
    seed: int
    text: str                    # question only (no "Problem N:"), plain text, states rounding + units
    answer: Answer
    solution: str                # short worked solution, no trailing period, <= 300 chars
    hint: str                    # a first step; must not contain answer.display
    mistakes: tuple[Mistake, ...] = ()

@dataclass(frozen=True)
class Skill:
    id: str                      # "<subject>.<name>", e.g. "maths.pythagoras"
    subject: str
    title: str                   # human label, used as topic label for «My own topic»
    aliases: tuple[str, ...]     # lowercase phrases for free-text matching
    generate: Callable[[int, int], Problem]   # (level 1..5, seed) -> Problem; pure & deterministic (random.Random(seed))

@dataclass(frozen=True)
class Topic:
    id: str                      # stable, stored in DB
    label: str                   # exact button text
    skills: tuple[str, ...]      # skill ids, non-empty
    level_map: tuple[int, int, int, int, int] = (1, 2, 3, 4, 5)   # student level (index+1) -> generator level
    exam: bool = False           # True only for past-paper topics

@dataclass(frozen=True)
class YearSpec:
    rows: tuple[tuple[Topic, ...], ...]          # keyboard rows, 1–2 topics each
    past_paper_level_map: tuple[int, int, int, int, int] = (2, 3, 3, 4, 5)

@dataclass(frozen=True)
class Subject:
    id: str                      # "maths"
    title: str                   # exact button text, "Maths"
    order: int                   # button order (ascending)
    years: dict[int, YearSpec]   # only years with content

def problem_to_json(p: Problem) -> str: ...      # json.dumps of nested dataclasses (tuples -> lists)
def problem_from_json(s: str) -> Problem: ...    # exact inverse: problem_from_json(problem_to_json(p)) == p
```

### 2.2 `tutor/content/registry.py`

```python
class RegistryError(ValueError): ...

class Registry:
    def register(self, subject: Subject, skills: Iterable[Skill]) -> None
    def subjects_for_year(self, year: int) -> list[Subject]        # sorted by .order; [] if none
    def years(self) -> list[int]                                   # sorted years having >= 1 subject
    def subject(self, subject_id: str) -> Subject | None
    def skill(self, skill_id: str) -> Skill | None
    def skills_of(self, subject_id: str) -> list[Skill]            # registration order
    def topic_rows(self, subject_id: str, year: int) -> list[tuple[str, ...]]   # labels of YearSpec.rows; [] if none
    def topic_by_label(self, subject_id: str, year: int, label: str) -> Topic | None  # case-insensitive, trimmed; includes PAST_PAPER_LABEL
    def topic(self, topic_id: str) -> Topic | None                 # resolves regular, past-paper and "own:<skill_id>" ids
    def own_topic(self, skill_id: str) -> Topic                    # Topic(id="own:"+skill_id, label=skill.title, skills=(skill_id,))
    def match_skills(self, subject_id: str, text: str) -> list[str]  # best first; [] if none

def load_registry(banks: Iterable[str] = ()) -> Registry
```

- **`load_registry`** imports every module in `tutor.subjects` found by `pkgutil.iter_modules`, skipping names starting with `_`, in name order. It calls `module.register(reg)` on each, then `register_bank(reg, path)` for each bank. Every call returns a new Registry. **Adding a subject means adding one file with `def register(reg): reg.register(Subject(...), [Skill(...), ...])`.**
- **Past-paper topic** per (subject, year): `Topic(id=f"{sid}.y{year}.past_paper", label=PAST_PAPER_LABEL, skills=<all skills in that year's rows, de-duplicated, in order>, level_map=spec.past_paper_level_map, exam=True)`.
- **`register` raises `RegistryError` when:**
  - a subject or skill id is duplicated;
  - `skill.subject != subject.id`;
  - a topic references an unknown skill;
  - a topic id is duplicated;
  - a label is duplicated within a (subject, year);
  - a label equals a reserved label: `Past paper practice`, `My own topic`, `🎓 Change year`, `📘 Change subject`;
  - a `level_map` is not 5 values in 1..5;
  - a row has 0 or more than 2 topics.
- **`match_skills`:**
  - Normalise text and aliases the same way: lowercase; `’`→`'`; `½`→`1/2`; remove spaces around `=`; collapse whitespace.
  - An alias matches if it occurs with no letter or digit on either side (an optional trailing `s` is allowed).
  - Score = length of the longest matching alias. Sort by score descending; ties go by registration order.
  - Only the given subject's skills are searched.

### 2.3 `tutor/content/checker.py`

```python
@dataclass(frozen=True)
class Verdict:
    status: str          # "correct" | "wrong" | "unparsed" | "unmarkable"
    feedback: str = ""   # for "wrong": form-violation text or matched Mistake.feedback; "" otherwise. No trailing period.

FORM_STANDARD   = "That's the right value, but it needs to be in standard form (a × 10^n, with 1 ≤ a < 10)"
FORM_FACTORISED = "That's equivalent, but the question asks you to factorise — write it as brackets multiplied together"
FORM_EXPANDED   = "That's equivalent, but the question asks you to expand — multiply out all the brackets"
FORM_SIMPLEST   = "That's equivalent, but it isn't in its simplest form yet"

def check(answer: Answer, text: str, mistakes: Sequence[Mistake] = ()) -> Verdict
def parse_number(s: str) -> float | None
def parse_fraction(s: str) -> Fraction | None
```

**Rules**
- `rubric` always returns `unmarkable`.
- `wrong` means the text parsed but does not match. In that case, if `check(m.answer, text).status == "correct"` for some mistake `m`, then `feedback = m.feedback` (first match wins). Form-violation feedback takes priority.
- **Extraction:** use the last non-empty line; if it fails to parse, try earlier lines from the bottom up. Within a line, use the text after the last `=` or `≈`. Strip prefixes such as `answer:`, `ans`, `so`, `therefore`. Currency (`£ $ €`) and trailing units (letters, `° % / ² ³ ⁻ ¹ ^ Ω µ` and digits after a unit letter) are stripped for number kinds.
- **Number tolerance:** with `dp`, accept if |v − exact| ≤ 0.5·10^−dp (+1e−9). With `sf`, the tolerance is 0.5·10^(floor(log10|exact|) − sf + 1). With neither, accept if |v − exact| ≤ 1e−6·max(1, |exact|).
- **Number formats accepted:** integers, decimals, `+`/`−` (U+2212), thousands (`1,200` = 1200), decimal comma (`4,5` = 4.5 when 1–2 digits follow), `a/b`, mixed `a b/c`, standard form (`3.2 × 10^4`, `3.2x10^4`, `3.2*10^4`, `3.2 × 10⁴`, `10^(-4)`, `10^−4`, `10⁻⁴`), `k π` / `kpi` (= k·π), percent sign stripped. Words are not numbers.
- **Fraction kind:**
  - Exact equivalents are accepted: fraction, mixed number, terminating decimal.
  - For a non-terminating value, a decimal with ≥ 2 d.p. is accepted if it is within half a unit of its last place.
  - With `form="simplest"`, only a/b in lowest terms, an integer, or a mixed number in lowest terms is correct. An equivalent non-simplest fraction or a decimal gives `wrong` with `FORM_SIMPLEST`.
- **Set and assign kinds:**
  - Split the last line on `,` `;` ` and ` ` or ` `&`. In ordered sets `:` also separates.
  - If that does not give the expected count, take the last *n* `<letter> = number` matches anywhere in the text.
  - Set: compare as a multiset (or a list when `ordered`).
  - Assign: find each variable's last `var = number` anywhere in the text. If that fails, fall back to positional order (`(3, -1)`).
- **Expr kind:**
  - Parsed with mathexpr. Only `answer.var` is allowed; any other letter means `unparsed`.
  - If equivalent, check the form: `expanded` with an unexpanded form gives `wrong` + `FORM_EXPANDED`; `factorised` with a non-product gives `wrong` + `FORM_FACTORISED`.
- **Ratio kind:**
  - Integers `a:b[:c]` with spaces allowed.
  - `simplest`: the exact parts in lowest terms are correct; a proportional but non-simplest ratio gives `wrong` + `FORM_SIMPLEST`.
  - `any`: any proportional ratio is correct.

**Acceptance table (test-dev asserts these exactly; C = correct, W = wrong, WF = wrong with the named form feedback, U = unparsed)**

| Answer | C | W | WF | U |
|---|---|---|---|---|
| number 4.0 | `4`, `x = 4`, `x=4`, `4.0`, `Answer: 4`, `3x = 12\nx = 4`, `4 cm`, `+4`, `x = 4\nthanks` | `5`, `x = -4` | — | `four`, `I think so`, `` |
| number 12.5 dp1, display `12.5 m/s` | `12.5`, `12.5 m/s`, `12.5m/s`, `v = 12.5 m/s`, `12.50`, `12.49` | `12.6`, `125` | — | — |
| number 7.0710678 dp1 | `7.1`, `7.07`, `7.071` | `7.0`, `7.2` | — | — |
| number 1234.5678 sf3 | `1230`, `1,230`, `1.23 × 10^3` | `1240`, `1200` | — | — |
| number 32000 form standard | `3.2 × 10^4`, `3.2x10^4`, `3.2 x 10^4`, `3.2*10^4`, `3.2 × 10⁴` | `3.2 × 10^5` | `32000`, `32 × 10^3` → FORM_STANDARD | — |
| number 0.00045 form standard | `4.5 × 10^-4`, `4.5×10^(-4)`, `4.5 x 10^−4`, `4.5 × 10⁻⁴` | `4.5 × 10^-3` | `0.00045` | — |
| number 78.5398 dp1 | `78.5`, `25π`, `25pi` | `78.6` | — | — |
| fraction "3/4" | `3/4`, `6/8`, `0.75`, `x = 3/4`, ` 3 / 4 ` | `4/3`, `0.7` | — | `three quarters` |
| fraction "7/4" | `1 3/4`, `7/4`, `1.75` | `1 1/4` | — | — |
| fraction "1/3" | `1/3`, `2/6`, `0.33`, `0.333` | `0.3`, `0.34` | — | — |
| fraction "3/4" simplest | `3/4` | `2/3` | `6/8`, `0.75` → FORM_SIMPLEST | — |
| set ["2","-3"] | `x = 2, x = -3`, `x=-3, x=2`, `x = 2 or x = -3`, `2 and -3`, `-3, 2`, `x = 2\nx = -3`, `(x-2)(x+3)=0\nx=2\nx=-3` | `x = 2`, `x = 2, x = 3`, `x = -2, x = 3` | — | `both of them` |
| set ["20","30"] ordered | `£20 and £30`, `20, 30`, `£20, £30`, `20:30` | `30 and 20`, `£25 and £25` | — | — |
| assign {x:"3", y:"-1"} | `x = 3, y = -1`, `y=-1, x=3`, `x=3 and y=-1`, `(3, -1)`, `x = 3\ny = -1` | `x = -1, y = 3`, `x = 3, y = 1` | — | `x is three` |
| expr "x**2+5*x+6" expanded | `x² + 5x + 6`, `x^2+5x+6`, `x**2 + 5*x + 6`, `5x + x^2 + 6`, `6+5x+x²`, `(x+2)(x+3) = x^2+3x+2x+6 = x^2+5x+6` | `x^2+6x+5`, `x^2+5x` | `(x+2)(x+3)` → FORM_EXPANDED | `no idea how` |
| expr "(x+2)*(x+3)" factorised | `(x+2)(x+3)`, `(x+3)(x+2)`, `(2+x)(3+x)` | `(x-2)(x-3)`, `(x+1)(x+6)` | `x^2+5x+6` → FORM_FACTORISED | — |
| expr "3*n+2" var n | `3n+2`, `nth term = 3n + 2`, `2 + 3n` | `3n`, `n+3` | — | `x+2` |
| ratio [2,3] simplest | `2:3`, `2 : 3` | `3:2` | `4:6` → FORM_SIMPLEST | — |
| ratio [2,3] any | `4:6` | `3:2` | — | — |
| rubric | → `unmarkable` for any text | | | |

### 2.4 `tutor/content/mathexpr.py` (safe evaluator; never `eval`/`exec`/`compile`-with-builtins)

```python
class ExprError(ValueError): ...
def parse(s: str, var: str = "x") -> ast.Expression        # raises ExprError
def evaluate(tree: ast.Expression, env: dict[str, float]) -> float   # raises ExprError (div by zero, overflow, |exponent| > 10)
def equivalent(a: str, b: str, var: str = "x") -> bool | None       # None if either fails to parse
def is_expanded(s: str, var: str = "x") -> bool
def is_factorised(s: str, var: str = "x") -> bool
POINTS = (-2.3, -1.1, 0.7, 1.9, 3.4, 5.6)
```

- **Preprocessing:**
  - `^`→`**`; `²`/`³`→`**2`/`**3`; `×`/`·`→`*`; `÷`→`/`; `−`→`-`; `π`/`pi`→`math.pi` constant.
  - Implicit `*` is inserted between number→var, number→`(`, var→`(`, `)`→`(`, `)`→var, `)`→number, var→var.
  - Then `ast.parse(mode="eval")`.
- **Allowed nodes:** Expression, BinOp(Add, Sub, Mult, Div, Pow), UnaryOp(UAdd, USub), int/float Constant, Name == var. Anything else raises ExprError.
- **Limits:** input ≤ 200 chars, ≤ 200 AST nodes, constant power exponent |e| ≤ 10. `9**9**9` and `x**99999` must fail fast.
- **Equivalence:** at each of `POINTS`, |a−b| ≤ 1e−6·max(1, |a|, |b|). Points that raise are skipped; at least 3 valid points are needed, otherwise the result is not equivalent.
- **`is_expanded`:** no Mult/Pow node has an operand that is an Add/Sub containing `var`.
- **`is_factorised`:** the root (after unary minus) is a Mult chain or a Pow, and at least one factor is an Add/Sub containing `var`.

### 2.5 `tutor/content/bank.py` (JSON question banks for future subjects; not auto-loaded in v1)

```python
class BankError(ValueError): ...
def load_bank(path: str) -> tuple[Subject, list[Skill]]
def register_bank(reg: Registry, path: str) -> None
```

Format:

```json
{
  "subject": {"id": "testsubj", "title": "Test Subject", "order": 99},
  "skills": [
    {"id": "testsubj.adding", "title": "Adding", "aliases": ["adding", "addition"],
     "questions": [
       {"level": 1, "text": "What is 2 + 3?",
        "answer": {"kind": "number", "display": "5", "value": 5},
        "solution": "2 + 3 = 5", "hint": "Count on from 2",
        "mistakes": [{"answer": {"kind": "number", "display": "6", "value": 6}, "feedback": "Count again carefully"}]}
     ]}
  ],
  "years": {"10": {"rows": [[{"id": "testsubj.y10.basics", "label": "Basics", "skills": ["testsubj.adding"], "level_map": [1,2,3,4,5]}]],
                   "past_paper_level_map": [1,1,1,1,1]}}
}
```

- **Answer keys** are the `Answer` field names; missing keys take the defaults. Optional keys are `level_map`, `past_paper_level_map` and `mistakes`.
- **Generated skill:** `generate(level, seed)` picks `random.Random(seed).choice` from the questions at that level. If none exist, it uses the nearest level, preferring lower. It returns a `Problem(level=level, seed=seed, …)`.
- **Validation (raises `BankError`, message includes the JSON path):** missing fields, unknown kind, level not in 1..5, a non-rubric display that is not judged `correct` by `check`, a skill with no questions.

### 2.6 `tutor/content/__init__.py` exports

`Answer, Mistake, Problem, Skill, Topic, YearSpec, Subject, PAST_PAPER_LABEL, MY_OWN_TOPIC_LABEL, problem_to_json, problem_from_json, check, Verdict, Registry, RegistryError, load_registry, load_bank, register_bank, BankError`

---

## 3. Core contracts (api-dev-core implements)

### 3.1 `tutor/messages.py`

```python
Keyboard = tuple[tuple[str, ...], ...]

@dataclass(frozen=True)
class Incoming:
    chat_id: int
    user_id: int
    text: str | None            # None for non-text (photo, sticker…)
    first_name: str = ""
    username: str = ""
    chat_type: str = "private"

@dataclass(frozen=True)
class Outgoing:
    chat_id: int
    text: str
    keyboard: Keyboard | None = None    # reply keyboard; None = leave unchanged
    remove_keyboard: bool = False
```

### 3.2 `tutor/config.py`

```python
REPO_ROOT: str   # parent dir of tutor/
@dataclass(frozen=True)
class Config:
    token: str | None = None
    owner_id: int | None = None
    anthropic_api_key: str | None = None
    model: str = "claude-haiku-5-5"
    db_path: str = ":memory:"
    llm_daily_limit: int = 40
    flood_per_minute: int = 20
def load_config(environ: Mapping[str, str] | None = None) -> Config
```

- **Lookup:** for each key, read `environ` first (default `os.environ`), then the `.env` file. The file is `environ["TUTOR_ENV_FILE"]` if set, otherwise `REPO_ROOT/.env`. Parsing follows `bot.load_token`: `KEY=value`, quotes stripped, comment and blank lines ignored.
- **Token:** `BOT=<name>` → token key `TELEGRAM_BOT_TOKEN_<NAME>`, otherwise `TELEGRAM_BOT_TOKEN`.
- **`owner_id`:** `int(TUTOR_OWNER_ID)` if it is a valid integer, otherwise None (log a warning).
- **`db_path`:** `TUTOR_DB`, otherwise `data/tutor.db`, or `data/tutor-<bot lowercase>.db` when BOT is set. Relative paths are resolved against REPO_ROOT.
- **`llm_daily_limit`:** `int(TUTOR_LLM_DAILY_LIMIT or 40)`; an invalid value falls back to 40.

### 3.3 `tutor/db.py`: schema (applied with `CREATE … IF NOT EXISTS`; `meta.schema_version = '1'`)

```sql
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);        -- schema_version, tg_offset
CREATE TABLE IF NOT EXISTS codes (
  code TEXT PRIMARY KEY, created_at REAL NOT NULL, used_by INTEGER, used_at REAL);
CREATE TABLE IF NOT EXISTS students (
  chat_id INTEGER PRIMARY KEY, first_name TEXT NOT NULL DEFAULT '', username TEXT NOT NULL DEFAULT '',
  verified INTEGER NOT NULL DEFAULT 0,
  step TEXT NOT NULL DEFAULT 'code' CHECK (step IN ('code','year','subject','topic','own_topic','lesson')),
  year INTEGER NOT NULL DEFAULT 11, subject TEXT, topic TEXT,
  created_at REAL NOT NULL, last_seen REAL NOT NULL);
CREATE TABLE IF NOT EXISTS progress (
  chat_id INTEGER NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL,
  level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5), PRIMARY KEY (chat_id, subject, topic));
CREATE TABLE IF NOT EXISTS pending (
  chat_id INTEGER PRIMARY KEY, subject TEXT NOT NULL, topic TEXT NOT NULL, skill TEXT NOT NULL,
  level INTEGER NOT NULL, gen_level INTEGER NOT NULL, seed INTEGER NOT NULL, problem_no INTEGER NOT NULL,
  problem_json TEXT NOT NULL, hints_given INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL,
  skill TEXT NOT NULL, level INTEGER NOT NULL, gen_level INTEGER NOT NULL,
  correct INTEGER NOT NULL, skipped INTEGER NOT NULL DEFAULT 0, ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_chat_ts ON attempts (chat_id, ts);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, kind TEXT NOT NULL,
  text TEXT NOT NULL, ts REAL NOT NULL, reviewed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS llm_usage (
  chat_id INTEGER NOT NULL, day TEXT NOT NULL, calls INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (chat_id, day));
```

```python
@dataclass
class Student: chat_id: int; first_name: str; username: str; verified: bool; step: str; year: int
               subject: str | None; topic: str | None; created_at: float; last_seen: float
@dataclass
class Pending: chat_id: int; subject: str; topic: str; skill: str; level: int; gen_level: int; seed: int
               problem_no: int; problem: Problem; hints_given: int; created_at: float
@dataclass
class Attempt: chat_id: int; subject: str; topic: str; skill: str; level: int; gen_level: int
               correct: bool; skipped: bool; ts: float
@dataclass
class Flag: id: int; chat_id: int; kind: str; text: str; ts: float; reviewed: bool

class Store:
    def __init__(self, path: str)            # ":memory:" ok; makes parent dir; isolation_level=None; WAL for files
    def close(self) -> None
    def transaction(self) -> ContextManager  # BEGIN IMMEDIATE / COMMIT / ROLLBACK on exception
    def get_offset(self) -> int; def set_offset(self, offset: int) -> None
    def add_codes(self, n: int, now: float) -> list[str]
    def redeem_code(self, code: str, chat_id: int, now: float) -> bool   # code already normalised; one-time
    def count_unused_codes(self) -> int
    def get_student(self, chat_id: int) -> Student | None
    def upsert_seen(self, chat_id: int, first_name: str, username: str, now: float) -> Student
    def save_student(self, s: Student) -> None
    def list_students(self, limit: int = 50) -> list[Student]          # last_seen desc
    def delete_student_data(self, chat_id: int) -> None  # students, progress, pending, attempts, flags, llm_usage; codes.used_by -> NULL
    def get_level(self, chat_id, subject, topic) -> int                # default 1
    def set_level(self, chat_id, subject, topic, level: int) -> None
    def levels(self, chat_id) -> list[tuple[str, str, int]]
    def get_pending(self, chat_id) -> Pending | None
    def set_pending(self, p: Pending) -> None
    def clear_pending(self, chat_id) -> None
    def add_attempt(self, a: Attempt) -> None
    def recent_attempts(self, chat_id, limit: int = 10) -> list[Attempt]   # newest first
    def attempt_stats(self, since: float, chat_id: int | None = None) -> tuple[int, int]   # (total, correct)
    def add_flag(self, chat_id, kind, text, now) -> int                # text truncated to 500
    def unreviewed_flags(self) -> list[Flag]
    def mark_flags_reviewed(self, ids: Iterable[int]) -> None
    def llm_calls(self, chat_id, day: str) -> int
    def incr_llm_calls(self, chat_id, day: str) -> None
    def llm_calls_total(self, day: str) -> int
```

`day` = `time.strftime("%Y-%m-%d", time.gmtime(now))` (UTC).

### 3.4 `tutor/intents.py` (pure functions)

```python
def normalize(text: str) -> str                # lowercase, ’→', collapse spaces, strip punctuation except ' % = / ^ + - * ( ) . ,
def command_name(text: str) -> str | None      # "/codes@Bot 5" -> "/codes"; None if not starting with "/"
def normalize_code(text: str) -> str | None    # remove spaces/hyphens, upper; returns it if not "/..." and fullmatch [A-Z0-9]{6,12}
def parse_year(text: str) -> tuple[int, str] | None   # "Year 7"/"year 7"/"Y7"/"7" -> (7,"Year 7"); "Year 1–6"/"Year 1-6" -> (6,"Year 1–6"); 1..13 only
def is_distress(text: str) -> bool
def is_cheat_request(text: str) -> bool
def intent(text: str) -> str | None            # "hint" | "skip" | None; None whenever text contains a digit
```

**Intent order:**
1. Exact SKIP set: `skip, next, pass, i don't know, i dont know, idk, dunno, no idea, give up, i give up, show answer, show me the answer`
2. Exact HINT set: `hint, a hint, give me a hint, help, help me, stuck, i'm stuck, im stuck, i don't get it, i dont get it, i don't understand, i dont understand, how do i start, what do i do, explain, ?`
3. Contains a HINT phrase: `hint, help, stuck, don't get, dont get, don't understand, dont understand, how do i, how to`
4. Contains a SKIP phrase: `skip, don't know, dont know, idk, give up, no idea`

**Distress phrases (contains, after normalize):** `kill myself, kms (whole word), want to die, wanna die, end my life, end it all, suicide, suicidal, self harm, self-harm, selfharm, hurt myself, hurting myself, cut myself, cutting myself, don't want to live, dont want to live, no reason to live, better off dead, better off without me, nobody would care if i, being bullied, abused, abusing me, not safe at home, scared to go home`.

**Cheat phrases:** `do my homework, do my hw, do my test, do this test for me, do it for me, write my essay, write an essay for me, write my coursework, test answers, exam answers, answers to the test, answers to the exam, answers for the test, answers for the exam, answer key, give me the answers`.

### 3.5 `tutor/llm.py`

```python
class LLM(Protocol):
    def complete(self, system: str, user: str, max_tokens: int = 300) -> str | None: ...

class ClaudeLLM:   # POST https://api.anthropic.com/v1/messages; headers x-api-key, anthropic-version: 2023-06-01, content-type: application/json
    def __init__(self, api_key: str, model: str, timeout: float = 20.0) -> None
    def complete(self, system, user, max_tokens=300) -> str | None   # never raises; joins text blocks; logs warning on failure

def system_prompt(subject_title: str, year: int, mode: str) -> str     # mode: "hint" | "chat" | "feedback" | "pick" | "mark"
def tutor_text(llm, mode, problem: Problem, student_text: str, subject_title: str, year: int) -> str | None
def pick_skill(llm, text: str, skills: list[tuple[str, str]]) -> str | None   # must return one of the given ids exactly, else None
def mark_rubric(llm, problem: Problem, student_text: str) -> tuple[int, str] | None   # expects JSON {"marks": int, "feedback": str}; clamps 0..max_marks
def clean(text: str, max_words: int = 80) -> str        # strip Markdown chars (* _ ` #), trim, cut to 80 words + "…"
def leaks_answer(text: str, answer: Answer) -> bool     # display (lowercased, no spaces, len>=2) is a substring, or any number in display appears as a standalone token
```

**Base system prompt (verbatim):**

> You are a friendly, patient tutor for secondary-school students (age 11–16) in the British school system, helping with {subject} (Year {year}). Reply in simple English, plain text only (no Markdown, no LaTeX), at most 80 words. Only help with schoolwork; if the student goes off-topic, kindly steer them back to the problem. Never do homework, write essays or give test answers for them — teach step by step instead. Never ask for personal information. The correct answer below was verified by a computer and is always right: never contradict it.

**Mode suffixes:**
- **hint/chat:** "Do NOT reveal the answer or the final value. Give at most one next step."
- **feedback:** "The student's answer was wrong. In 1–2 sentences, kindly explain where their working most likely went wrong. Do not start with 'Not quite' and do not restate the correct answer."

**User message:** `Problem: {text}\nVerified answer: {display}\nWorked solution: {solution}\nStudent's message: {student_text}`

**Filtering:** for hint and chat, return None if `leaks_answer`. Never send names or chat ids to the API.

### 3.6 `tutor/owner.py`

```python
OWNER_COMMANDS = ("/codes", "/students", "/student", "/reset", "/flags", "/stats")
def handle_owner(cmd: str, args: list[str], *, store: Store, now: float, registry: Registry) -> list[str]
```

It returns texts, which the engine wraps into `Outgoing(owner_id, text)`. The formats are in §4.3.

### 3.7 `tutor/engine.py`

```python
class Engine:
    def __init__(self, store: Store, config: Config, registry: Registry | None = None,
                 llm: LLM | None = None, clock: Callable[[], float] = time.time,
                 rng: random.Random | None = None) -> None     # registry None -> load_registry()
    def handle(self, msg: Incoming) -> list[Outgoing]
```

`handle`:
- returns `[]` for any `chat_type != "private"`;
- otherwise runs `with store.transaction(): return self._handle(msg)`;
- on any exception: `log.exception` and return `[Outgoing(msg.chat_id, ERROR)]` (the DB is rolled back).

**`_handle` order:**
`now = clock()`, `text = (msg.text or "")[:2000].strip()`, `cmd = command_name(text)`

1. **Owner command:** `owner_id` set, `msg.user_id == owner_id` and `cmd in OWNER_COMMANDS` → owner replies. Non-owners go on to the normal flow.
2. **Flood control:** at most `flood_per_minute` messages per chat in a sliding 60 s window, kept in memory. Extra messages return `[]`. The owner is exempt.
3. `st = store.upsert_seen(...)` (a new student gets year 11 and step `code`).
4. **`/delete_my_data`:** `delete_student_data` → `[Outgoing(DELETED, remove_keyboard=True)]`.
5. **`/start`:** not verified → step=code → `[Outgoing(CODE_REQUEST, remove_keyboard=True)]`. Verified → clear pending, step=subject → `subject_reply(st)` (no code needed; if the year has no subjects this returns YEAR_NOT_READY + YEAR_KB as usual).
6. **Distress** (`is_distress(text)`): `add_flag("distress")` → `[Outgoing(DISTRESS, keyboard=current_kb(st))]` (None if not verified), plus `Outgoing(owner_id, OWNER_FLAG_ALERT)` if `owner_id` is set. The LLM is never called. Pending is kept and no problem is sent.
7. **Not verified:**
   - `normalize_code` returns None (including non-text) → `[CODE_REQUEST]`.
   - `redeem_code` fails → `[CODE_BAD]`.
   - Otherwise verified=True, step=subject → `[CODE_OK] + subject_reply(st)`.
8. **Non-text:** `msg.text is None` → `[TEXT_ONLY + current_kb]`.
9. **Change buttons:**
   - `🎓 Change year` or `⚙️ Change year / topic` → clear pending, step=year → `[YEAR_ASK + YEAR_KB]`.
   - `📘 Change subject` → clear pending, step=subject → `subject_reply(st)`.
10. **Topic buttons:** if the step is topic, own_topic or lesson and the subject is valid for the year:
    - `My own topic` → clear pending, step=own_topic → `[OWN_TOPIC_ASK + topic_kb]`;
    - `t = registry.topic_by_label(...)` found → `start_topic(t)`.
11. **Cheat request** (`is_cheat_request`) → `[CHEAT + current_kb]`.
12. **By step:**
    - **year:** if `parse_year` fails → `[YEAR_ASK + YEAR_KB]`. If the year has no subjects → `[YEAR_NOT_READY(label) + YEAR_KB]` (year unchanged). Otherwise set year, step=subject → `subject_reply`.
    - **subject:** a case-insensitive title match among `subjects_for_year` → set subject, topic=None, step=topic → `[TOPIC_ASK + topic_kb]`. Otherwise `subject_reply`.
    - **topic:** `[TOPIC_ASK + topic_kb]`.
    - **own_topic:** `ids = match_skills(subject, text)`. If empty and the LLM is allowed, use `pick_skill` over `skills_of(subject)`. If a skill is found → `start_topic(registry.own_topic(id))`. Otherwise `[OWN_TOPIC_NONE + topic_kb]`.
    - **lesson:** `lesson_reply` (below). If there is no pending problem, set step=topic and return `[TOPIC_ASK + topic_kb]`.

**Helper behaviour**
- **`subject_reply(st)`:** if there are no subjects for the year, step=year → `[YEAR_NOT_READY("Year N") + YEAR_KB]`. Otherwise `[SUBJECT_ASK(year) + subject_kb]`. If the stored subject or topic is unknown to the registry, fall back to the subject or topic step.
- **`start_topic(t)`:**
  - step=lesson, topic=t.id;
  - L = max(1, get_level − 1), then `set_level(L)`;
  - skill = `rng.choice(t.skills)`;
  - returns `[TOPIC_START(t.label), problem_msg(problem_no=1)]`.
- **`next_problem(...)`:**
  - `gen = t.level_map[L−1]`, `seed = rng.randrange(1, 2**31)`;
  - re-seed up to 3 times if the text equals the previous problem's text;
  - `set_pending`;
  - message = `PROBLEM` or `PROBLEM_EXAM` (when `t.exam`; marks = {1:1, 2:2, 3:2, 4:3, 5:4}[gen]) + topic_kb.
- **`lesson_reply(p)`:**
  - **hint:**
    - First hint → `HINT`.
    - Later hints → if `tutor_text("hint")` is allowed and returns text → `HINT_LLM`, otherwise `HINT_AGAIN`.
    - Then `hints_given += 1`. No new problem.
  - **skip:** record an attempt (correct=0, skipped=1), L=max(1, L−1) → `[SKIP, next problem (same skill, no+1)]`.
  - **rubric:**
    - `mark_rubric` allowed and returns (m, fb) → if m == max_marks, `CORRECT(fb)` + level up + other skill; otherwise `WRONG(fb, display)` + level down + same skill. An attempt is recorded either way.
    - Otherwise → `[UNMARKABLE(display), next problem (same level and skill)]`, with no attempt recorded.
  - **`v = check(answer, text, mistakes)`:**
    - **correct:** record attempt, L=min(5, L+1) → `[CORRECT(solution), next problem (another skill of the topic if it has more than one)]`.
    - **wrong:** record attempt, L=max(1, L−1); `why` = `v.feedback`, or `tutor_text("feedback")`, or `WHY_FALLBACK(solution)` → `[WRONG(why, display), next problem (same skill)]`.
    - **unparsed:** `tutor_text("chat")` allowed and returns text → `[LLM_CHAT + topic_kb]`. Otherwise: `UNPARSED` if the text contains a digit or any of `= + - * / ^ ² √ π`, else `OFFTOPIC(subject.title, problem_no)`.
- **LLM allowed:** `llm is not None and store.llm_calls(chat, day) < config.llm_daily_limit`. Call `incr_llm_calls` before every LLM call. A None result means the fixed fallback is used silently.
- **Text joining:** `solution`, `why` and `feedback` have trailing `. ` stripped before being put into the templates.
- **Keyboards:** only the last Outgoing of a reply carries a keyboard. `current_kb(st)` is: code → None; year → YEAR_KB; subject → subject_kb; topic/own_topic/lesson → topic_kb.
- **Invariant:** for a verified student, the last message of every non-empty reply has a keyboard. The exceptions are ERROR, `/start` from an unverified chat, and `/delete_my_data`. That keyboard is either YEAR_KB, or it contains `🎓 Change year` and either `📘 Change subject` or the subject buttons.

### 3.8 `tutor/telegram.py`

```python
class TelegramError(Exception):
    def __init__(self, description: str, code: int | None = None, retry_after: int | None = None)
class TelegramAPI:
    def __init__(self, token: str, timeout: int = 35, opener=urllib.request.urlopen)
    def call(self, method: str, **params) -> object      # POST urlencoded; raises TelegramError (HTTP/API error, non-JSON body) or OSError
    def get_me(self) -> dict
    def get_updates(self, offset: int, timeout: int = 30) -> list[dict]   # allowed_updates=["message"]
    def send_message(self, params: dict) -> None
def parse_update(update: dict) -> Incoming | None         # None unless update["message"]; text None if no "text"
def to_send_params(out: Outgoing) -> list[dict]           # see below
def run_polling(api, engine: Engine, store: Store, *, sleep=time.sleep, should_stop=lambda: False) -> None
```

- **`to_send_params`:**
  - Split text into chunks of at most 4000 chars, at the last `\n` before the limit (a hard cut if there is none).
  - Each chunk is `{"chat_id", "text"}` with no `parse_mode`.
  - The last chunk only gets `reply_markup` = `json.dumps({"keyboard": [[{"text": b} ...]], "resize_keyboard": true, "is_persistent": true})`, or `json.dumps({"remove_keyboard": true})`.
- **`run_polling`:**
  - Read `offset = store.get_offset()` once at startup.
  - `get_updates` failure (OSError, TimeoutError, TelegramError) → log, `sleep(backoff)`, backoff 1→2→4…→60. A 409 is logged as "another getUpdates consumer is running".
  - For each update:
    - parse;
    - `engine.handle`;
    - send each param dict with up to 3 tries; 429 waits `retry_after`, network errors wait 1/2/4 s, 400/403 are not retried;
    - then `store.set_offset(update_id + 1)`, even if handling failed.
  - The loop only exits when `should_stop()` returns true.
  - Logs carry chat ids and events, never message texts.

### 3.9 CLI `tutor/__main__.py` (argparse)

- **`python3 -m tutor`:** needs a token, otherwise prints `Set TELEGRAM_BOT_TOKEN (env var or .env file)` (with the actual key name) and exits 1. Logs `LLM: on (model)` or `LLM: off`, and warns if `TUTOR_OWNER_ID` is missing. Builds `ClaudeLLM` if a key is set, then runs `run_polling`. Ctrl-C exits 0.
- **`python3 -m tutor --check`:** prints `Connected as @{username} (id {id})`, then `LLM: off (no ANTHROPIC_API_KEY)`, or after a 1-token test call, `LLM: ok ({model})` / `LLM: FAILED ({model})`.
- **`python3 -m tutor codes N`:** N in 1..1000. Prints exactly N lines (codes only) to stdout and exits 0. Needs no token and no network. Bad N → usage on stderr, exit 2.
- **`python3 -m tutor sample SKILL_ID [LEVEL] [N=3]`:** prints text, answer, solution and hint for N seeds. An unknown skill prints all skill ids to stderr and exits 2.
- Logging goes to stderr: `%(asctime)s %(levelname)s %(name)s: %(message)s`.

---

## 4. User-facing texts (`tutor/texts.py`): verbatim

### 4.1 Kept from CLAUDE.md (unchanged)

```
CODE_REQUEST  = "🔐 Please enter your access code to start the lesson."
CODE_BAD      = "❌ That code isn't valid. Please check it and try again."
CODE_OK       = "✅ Code accepted — welcome! You're all set."
YEAR_ASK      = "🎓 Great! Which year group are you in? Tap the button below (British school system, Year 1–13)."
TOPIC_ASK     = "📚 What are you working on right now? Here's what students usually study in Year {year} — tap one, or choose «My own topic»."
OWN_TOPIC_ASK = "✍️ Tell me what you'd like to practise and I'll set problems on it."
TOPIC_START   = "🎯 Got it — switching to «{topic}». Let's start with an easy one."
PROBLEM       = "Problem {n}: {text}\n\nSend me your answer (and show your working!) 😊"
CORRECT       = "✅ Correct! {solution}."
WRONG         = "❌ Not quite. {why}. Correct answer: {answer}"
```

**Removed:** the button `⚙️ Change year / topic` (still accepted as input). The year step after the code (it is now reached only through `🎓 Change year`).

### 4.2 New

```
SUBJECT_ASK    = "📘 Which subject would you like to study? (Year {year}, British curriculum)"
YEAR_NOT_READY = "🚧 Sorry — I don't have lessons for {year_label} yet. Please choose another year group."
PROBLEM_EXAM   = "Problem {n} ({marks} mark{s}): {text}\n\nSend me your answer (and show your working!) 😊"     # s = "" if marks == 1 else "s"
WHY_FALLBACK   = "Here's the method: {solution}"
HINT           = "💡 Hint: {hint}"
HINT_AGAIN     = "💡 Hint: {hint}\n\nStill stuck? Type «skip» and I'll show you the full solution."
HINT_LLM       = "💡 {text}"
LLM_CHAT       = "{text}"
SKIP           = "👀 No problem — here's how to do it: {solution}. Answer: {answer}"
UNPARSED       = "🤔 I couldn't find an answer in that. Put your final answer on the last line — or type «hint» for a hint, or «skip» to see the solution."
OFFTOPIC       = "🙂 Let's keep our focus on {subject}! Have a go at Problem {n} — or type «hint» for a hint, or «skip» to see the solution."
CHEAT          = "🙅 I can't do homework, write essays or give out test answers for you — but I can help you learn to do it yourself, step by step! Pick a topic below or choose «My own topic» and we'll practise together. 💪"
DISTRESS       = "💙 I'm really sorry you're feeling like this, and thank you for telling me. You don't have to deal with it on your own. Please talk to a parent, a teacher or another adult you trust as soon as you can. If you are in danger right now, contact your local emergency services straight away. I'm here to help with your schoolwork whenever you're ready."
OWN_TOPIC_NONE = "🤷 Sorry — I can't set problems on that yet. Tap one of the topics below, or describe what you'd like to practise in a different way."
UNMARKABLE     = "📝 I can't mark written answers automatically yet, so here's a model answer to compare with yours: {answer}"
TEXT_ONLY      = "📝 I can only read text for now — please type your answer."
DELETED        = "🗑️ Done — I've deleted your data. If you'd like to come back, send /start and enter a new access code."
ERROR          = "⚠️ Sorry, something went wrong. Please try again."
```

**Keyboards**

```
CHANGE_YEAR = "🎓 Change year"; CHANGE_SUBJECT = "📘 Change subject"; LEGACY_CHANGE = "⚙️ Change year / topic"
YEAR_KB = (("Year 7","Year 8","Year 9"), ("Year 10","Year 11","Year 12"), ("Year 13","Year 1–6"))   # en dash
subject_kb(titles) = titles in rows of 2 + ((CHANGE_YEAR,),)
    Year 11 -> (("Maths","Physics"),("🎓 Change year",));  Year 8 -> (("Maths",),("🎓 Change year",))
topic_kb(rows) = rows + (("Past paper practice","My own topic"), (CHANGE_YEAR, CHANGE_SUBJECT))
    Year 11 Maths -> (("GCSE Higher: algebra & functions","GCSE Higher: trig & geometry"),
                      ("GCSE Foundation: number","GCSE Foundation: geometry"),
                      ("Past paper practice","My own topic"), ("🎓 Change year","📘 Change subject"))
```

### 4.3 Owner texts

Dates are UTC, formatted `%Y-%m-%d %H:%M`. `name` = first_name + (` @username` if a username exists).

```
CODES        = "🔑 {n} new code{s}:\n{codes}"                    # one code per line
CODES_USAGE  = "Usage: /codes N (N = 1–50)"
NO_STUDENTS  = "No students yet."
STUDENTS     = "👥 Students ({n}):\n" + lines "{chat_id} · {name} · {✅ verified|⛔ not verified} · Year {year} · {subject or '—'} · last seen {date}"
STUDENT      = "👤 {name} (chat {chat_id})\nStatus: {status}\nYear {year} · Subject: {subject} · Topic: {topic}\nLevels: {topic}: L{level}; …\nAttempts: {total} ({correct} correct)\nRecent:\n" + lines "{datetime} {skill} L{level} {✅|❌|⏭}"
STUDENT_USAGE= "Usage: /student CHAT_ID";  RESET_USAGE = "Usage: /reset CHAT_ID"
NOT_FOUND    = "Student {chat_id} not found."
RESET_OK     = "✅ Student {chat_id} has been reset — they need a new code."
NO_FLAGS     = "No new flags."
FLAGS        = "🚩 {n} new flag{s}:\n" + lines "#{id} {datetime} {kind} · chat {chat_id} ({name}): {text}"   # then marked reviewed
FLAG_ALERT   = "🚩 Safety flag ({kind}) from {name} (chat {chat_id}):\n\"{text}\"\nUse /student {chat_id} for details."
STATS        = "📊 Stats\nStudents: {total} ({verified} verified, {active7} active in 7 days)\nAttempts: {today} today, {week} in 7 days ({acc}% correct)\nUnused codes: {codes}\nLLM calls today: {llm}\nUnreviewed flags: {flags}"
```

---

## 5. Content v1 (api-dev-content)

### General generator rules
- Use `random.Random(seed)` only; no global random. Retries are bounded (≤ 50); construct problems backwards from nice answers.
- Plain text only: use `×`, `÷`, `²`, `√`, `π`, `°`; no LaTeX or Markdown. Every rounding instruction is in the text ("Give your answer to 1 decimal place.").
- **Display:** must pass `check` and include units where natural (`12.5 m/s`, `24 cm²`). Equations use `x = 4`; standard form uses `3.2 × 10^4`; ordered shares use `£20 and £30`.
- **Hint** must not contain `display`. **Solution** has no trailing period and is at most 300 characters. **Mistakes** must never be judged correct, and any that coincide with the correct answer are dropped.
- **Size limits:** text ≤ 600 chars. Quadratic roots are distinct integers; simultaneous equation solutions are integers; `sf ≥ 2`; `dp ∈ {0,1,2,3}`.

### Maths skills
All levels 1–5; ids are fixed. Title and minimum aliases are given; each ladder runs L1 → L5.

- **`maths.percentages`**: "Percentages" (percentage, percentages, percent). Ladder: 10/25/50% of an amount → any % (1 d.p.) → % increase/decrease → % change → reverse % or compound interest (2 d.p.).
- **`maths.fractions`**: "Fractions" (fraction, fractions). Ladder: simplify (`simplest`) → add/subtract with same or related denominators → unlike denominators → multiply/divide → mixed numbers.
- **`maths.ratio`**: "Ratio" (ratio, ratios). Ladder: simplify (ratio `simplest`) → share in 2 parts (ordered set) → 3 parts → given one share find another → difference between shares.
- **`maths.hcf_lcm`**: "HCF and LCM" (hcf, lcm, highest common factor, lowest common multiple). Ladder: HCF small → LCM small → larger numbers → from prime factorisations → word problem.
- **`maths.standard_form`**: "Standard form" (standard form). Ladder: large number → standard form (`standard`) → small number (negative power) → standard form to ordinary → × and ÷ (`standard`) → + and − (`standard`).
- **`maths.area_perimeter`**: "Area and perimeter" (area, perimeter). Ladder: rectangle perimeter → rectangle/triangle area → parallelogram/trapezium → compound L-shape → missing length.
- **`maths.angles`**: "Angles" (angles, angle facts). Ladder: straight line → triangle → around a point / vertically opposite / isosceles → interior angle of a regular polygon → number of sides, or algebraic angles.
- **`maths.pythagoras`**: "Pythagoras' theorem" (pythagoras). Ladder: hypotenuse from a triple → hypotenuse (1 d.p.) → shorter side → distance between points → isosceles height or 3D.
- **`maths.circles`**: "Circles" (circle, circles, circumference). Ladder: C from d → C from r → A from r → A from d → r from A, or semicircle perimeter. All 1 d.p.
- **`maths.linear_equations`**: "Linear equations" (linear equations, solving equations). Ladder: one-step → two-step → brackets → unknown on both sides → fractions (fraction kind if needed).
- **`maths.expand_brackets`**: "Expanding double brackets" (expanding brackets, expand brackets, double brackets). Ladder: (x+a)(x+b) → with negatives → (ax+b)(x+c) → (x+a)² / (ax+b)(cx+d) → triple brackets. expr `expanded`.
- **`maths.factorise_quadratics`**: "Factorising quadratics" (factorising, factorise, factorising quadratics). Ladder: x²+bx+c → with negatives → difference of two squares → ax²+bx+c → ax² with negatives. expr `factorised`. Sign-swap mistakes are included.
- **`maths.solve_quadratics`**: "Solving quadratics" (solving quadratics, quadratic equations). Ladder: x² = k → already factorised = 0 → x²+bx+c = 0 → negatives → a > 1. Set kind.
- **`maths.simultaneous`**: "Simultaneous equations" (simultaneous equations, simultaneous). Ladder: x+y / x−y → add/subtract directly → multiply one equation → multiply both → negatives/rearranged. Assign {x, y}.
- **`maths.nth_term`**: "nth term" (nth term, sequences). Ladder: the 10th term (number) → nth term increasing (expr var n) → decreasing → which term equals a value → quadratic nth term.
- **`maths.trig_sides`**: "Trigonometry: missing sides" (sohcahtoa, trigonometry, trig). Ladder: sin → cos → tan → hypotenuse by dividing → elevation word problem. 1 d.p.
- **`maths.trig_angles`**: "Trigonometry: missing angles" (missing angle, inverse trig). Ladder: tan⁻¹ → sin⁻¹ → cos⁻¹ → word problem → two-step. 1 d.p.
- **`maths.sine_rule`**: "Sine rule" (sine rule). Ladder: side → side after angle sum → acute angle → word problem → angle sum then side.
- **`maths.triangle_area_sine`**: "Area of a triangle (½ab sin C)" (ab sin c). Ladder: direct → decimals → side from area → angle from area → parallelogram.
- **`maths.arcs_sectors`**: "Arcs and sectors" (arc length, sector, sectors, arcs). Ladder: quarter/semicircle arc → any arc → sector area → sector perimeter → angle or radius from arc/area.

### Maths topics

Topic ids are `maths.y{Y}.<slug>`.

**Years 10 and 11** (rows exactly as CLAUDE.md):

| Topic (slug) | Label | Skills | level_map |
|---|---|---|---|
| higher_algebra | GCSE Higher: algebra & functions | linear_equations, expand_brackets, factorise_quadratics, solve_quadratics, simultaneous, nth_term | (1,2,3,4,5) |
| higher_trig | GCSE Higher: trig & geometry | pythagoras, trig_sides, trig_angles, sine_rule, triangle_area_sine, arcs_sectors | (1,2,3,4,5) |
| foundation_number | GCSE Foundation: number | percentages, fractions, ratio, hcf_lcm, standard_form | (1,2,3,3,4) |
| foundation_geometry | GCSE Foundation: geometry | area_perimeter, angles, pythagoras, circles, trig_sides | (1,2,3,3,4) |

Past paper level map: (2,3,3,4,5).

**Years 7, 8 and 9:** rows are `("KS3: number & fractions","KS3: algebra")` and `("KS3: geometry","KS3: ratio & percentages")`.

| Topic (slug) | Label | Skills |
|---|---|---|
| ks3_number | KS3: number & fractions | fractions, hcf_lcm, + standard_form in Year 9 |
| ks3_algebra | KS3: algebra | linear_equations, nth_term, + expand_brackets in Year 9 |
| ks3_geometry | KS3: geometry | angles, area_perimeter, + circles in Years 8–9, + pythagoras in Year 9 |
| ks3_ratio | KS3: ratio & percentages | percentages, ratio |

| Year | level_map (all KS3 topics) | Past paper level map |
|---|---|---|
| Year 7 | (1,1,2,2,3) | (1,2,2,3,3) |
| Year 8 | (1,2,2,3,3) | (1,2,3,3,4) |
| Year 9 | (1,2,3,3,4) | (2,2,3,4,4) |

**Subject:** `Subject("maths", "Maths", order=10)`.

### Physics
`Subject("physics", "Physics", order=20)`, Years 10–11 only.

**Topics** (ids `physics.y{Y}.<slug>`), rows:
- `("Forces & motion","Energy")`:
  - `forces` → speed, acceleration, force, weight
  - `energy` → kinetic_energy, gpe, power
- `("Electricity","Density & pressure")`:
  - `electricity` → ohms_law, electrical_power, charge
  - `density_pressure` → density, pressure

level_map (1,2,3,4,5); past paper (2,3,3,4,5).

**Skills** (id: title (minimum aliases)), all number kind:
- `physics.speed`: Speed (speed, distance time)
- `physics.acceleration`: Acceleration (acceleration)
- `physics.force`: Force (F = ma) (f=ma, resultant force, newton's second law)
- `physics.weight`: Weight (W = mg) (weight, w=mg, gravitational field strength). The question states "Use g = 9.8 N/kg."
- `physics.kinetic_energy`: Kinetic energy (kinetic energy)
- `physics.gpe`: Gravitational potential energy (gpe, gravitational potential energy, potential energy). States g = 9.8 N/kg.
- `physics.power`: Power (power)
- `physics.ohms_law`: Ohm's law (V = IR) (ohm's law, ohms law, resistance, v=ir)
- `physics.electrical_power`: Electrical power (P = IV) (electrical power, p=iv)
- `physics.charge`: Charge (Q = It) (charge, q=it)
- `physics.density`: Density (density)
- `physics.pressure`: Pressure (pressure)

**Shared ladder:**
- L1: direct substitution, whole numbers
- L2: rearranging
- L3: one unit conversion (g→kg, cm→m, min→s, kJ→J, mA→A, cm²→m²)
- L4: rearranging plus conversion
- L5: two-step or standard-form values (`sf` 2–3)

Answers carry units in the display.

---

## 6. Tests (test-dev)

**Rules**
- Run with `python3 -m unittest discover -s tests`; the whole suite must take under 90 s.
- Write tests from this document, not from the code.
- Golden tests hard-code the verbatim texts from §4 and do not import `tutor/texts.py`, so a text change needs a deliberate test change.
- Do not fix the implementation. Report failures.

**`tests/helpers.py`**
- `FakeClock` (callable, `.advance(s)`).
- `FakeLLM(responses)`: returns queued items (str or None) and records `(system, user)` calls.
- `make_engine(llm=None, owner_id=999, limit=40, registry=None, path=":memory:")` returns `(engine, store, clock)` using `random.Random(7)`.
- `send(engine, chat, text, user=None)` builds an `Incoming`.
- `get_codes(engine, n)` sends `/codes n` as the owner and parses lines matching `^[A-HJ-NP-Z2-9]{8}$`.
- `answer_of(store, chat)` returns `store.get_pending(chat).problem.answer.display`.
- `perturb(answer) -> str`:
  - number: `value + max(1, |value|·0.5)`, written as `m × 10^e` when the form is standard;
  - fraction: +1;
  - set: first element → max + 1;
  - assign: first variable + 1;
  - expr: `f"({value})+1"`;
  - ratio: `parts[0]+1`.

**What each test file covers**
- **test_mathexpr:** implicit multiplication cases (`2x`, `3(x+1)`, `(x+1)(x+2)`, `x(x+1)`, `x²`, `2x²`, `-x`); equivalence; `is_expanded`/`is_factorised`. The attack inputs `__import__('os')`, `x**99999`, `9**9**9`, a 1000-char string, `((((…` and `x.real` must raise `ExprError` in under 1 s each.
- **test_checker:** every row of the §2.3 table, plus mistake feedback matching.
- **test_skills:** for every skill in `load_registry()` (iterate the registry; also assert that the 32 required ids exist), every level 1–5 and 200 seeds:
  - the problem is deterministic;
  - text, solution and hint are non-empty and within length limits;
  - the problem survives a JSON round-trip;
  - `check(answer, display)` is correct and `check(answer, perturb)` is not correct;
  - every mistake display is judged wrong with that mistake's feedback;
  - the hint does not contain the display when the display is ≥ 3 chars.

  Collect failures and assert once at the end, showing the first 10.
- **test_registry:**
  - topic_rows match §5 exactly for Years 7–11 and both subjects;
  - years() == [7, 8, 9, 10, 11];
  - Physics is absent for Years 7–9;
  - the past-paper topic contains the union of skills and `exam=True`;
  - `own_topic`;
  - match_skills for every required alias, including "electrical power" → electrical_power, "power" → power and "photosynthesis" → [];
  - `RegistryError` cases.
- **test_bank:** load the fixture; register it into a fresh registry, after which Year 10 subjects include "Test Subject"; generation is deterministic; `bank_invalid.json` raises `BankError`; a fixture with a wrong display is rejected.
- **test_flow (golden):**
  - hello → CODE_REQUEST; /start (unverified) → CODE_REQUEST + remove_keyboard; /start (verified, mid-lesson) → SUBJECT_ASK + subject keyboard, pending cleared, still verified, no new code needed; after owner /reset, /start → CODE_REQUEST;
  - wrong code → CODE_BAD;
  - code in lower case → [CODE_OK, SUBJECT_ASK(11) + kb];
  - Maths → TOPIC_ASK + exact keyboard;
  - topic → [TOPIC_START, Problem 1 …];
  - the code works only once (second chat gets CODE_BAD);
  - Change year and Change subject from every step (year, subject, topic, own_topic, lesson), including the legacy button;
  - Year 1–6 / 12 / 13 → NOT_READY and the year is unchanged;
  - Physics hidden in Year 8;
  - My own topic → match → TOPIC_START with the skill title; no match → OWN_TOPIC_NONE;
  - the keyboard invariant from §3.7 holds for every reply.
- **test_lesson:**
  - correct → level+1, problem_no+1;
  - wrong → level−1 and the same skill;
  - the WRONG text format;
  - form feedback appears in WRONG;
  - hint (first time and again) and skip (attempt recorded as skipped);
  - UNPARSED vs OFFTOPIC;
  - Past paper gives "Problem 1 (n mark(s)):";
  - attempts are recorded;
  - re-entering a topic starts at max(1, L−1);
  - a generator that raises (custom registry) → [ERROR], state rolled back, the next message works.
- **test_llm:**
  - FakeLLM is used for the wrong-answer "why", second hints, chat and pick_skill;
  - the prompt contains "Verified answer:" and no first name;
  - a leaking hint falls back to HINT_AGAIN;
  - a None result falls back silently;
  - the daily limit (limit=2) is respected and FakeLLM is not called beyond it;
  - rubric: marks == max → CORRECT, less → WRONG, no LLM → UNMARKABLE;
  - `clean` caps at 80 words;
  - `ClaudeLLM` with a fake urlopen (patch `urllib.request.urlopen`): correct headers and body, and errors return None.
- **test_safety:**
  - must-detect: "I want to kill myself", "i want to die", "I'm going to hurt myself", "I cut myself", "thinking about suicide", "i self harm", "I don't want to live anymore", "nobody would care if I disappeared", "I'm being bullied and I can't take it";
  - must-not-detect: "this homework is killing me", "I'm dying to know", "the angle is a right angle";
  - distress → DISTRESS + an owner alert + a flag; no problem sent; works before the code too; LLM never called;
  - cheat phrases → CHEAT (and "I did my homework", "can you check my answer" are not cheat);
  - /delete_my_data → DELETED, data gone, next message → CODE_REQUEST;
  - flood: the 21st message in 60 s → [] (owner exempt); after `clock.advance(61)` replies resume;
  - group chats → [].
- **test_owner:**
  - /codes 3 → 3 valid codes; /codes 0, /codes 51 and /codes abc → usage;
  - a non-owner sending /codes gets the normal flow and no codes are created;
  - /students, /student X, an unknown student, /reset (the student then needs a new code and the old code fails);
  - /flags lists flags and marks them reviewed, then shows "No new flags.";
  - /stats contains "Students:";
  - `/codes@Bot 2` works.
- **test_persistence:**
  - With a file DB in a tempdir: reach a lesson, close, open a new Store and Engine with a different rng, send the stored answer → CORRECT. Verification, year and level survive.
  - Offset set/get survives reopening.
- **test_telegram:**
  - parse_update (text, photo → text None, group, edited_message → None);
  - to_send_params (keyboard JSON, remove, no parse_mode, 9000 chars → 3 chunks with the markup on the last only);
  - run_polling with a fake api: the offset is saved, a get_updates exception leads to a backoff sleep and the loop continues, a 403 on send continues, and `should_stop` ends the loop.
- **test_config:** a temp `.env` file plus a `TUTOR_ENV_FILE` environ: env beats the file; `BOT=english` uses `TELEGRAM_BOT_TOKEN_ENGLISH` and `data/tutor-english.db`; defaults; a bad owner id → None.
- **test_cli:** run in a subprocess with cwd at the repo root, `TUTOR_DB` set to a temp file and `TUTOR_ENV_FILE` set to a nonexistent path:
  - `codes 3` → exit 0, exactly 3 lines, and the codes are redeemable via an Engine on the same DB;
  - `codes 0` → exit 2;
  - `--check` with no token → non-zero exit and the "Set TELEGRAM_BOT_TOKEN" message;
  - `sample maths.pythagoras 2 1` → exit 0;
  - an unknown skill → exit 2.

---

## 7. Docs (api-dev-core)

### CLAUDE.md (English)
Sections in order:
1. What this is: one engine `tutor/`, all subjects as modules.
2. Run: environment variables table, `python3 -m tutor`, `--check`.
3. Codes: when Alan says "дай N кодов", run `python3 -m tutor codes N` and show the codes only in the Claude chat.
4. Owner commands.
5. Adding a subject: one file in `tutor/subjects/` with `register(reg)`, or a JSON bank; property tests cover it automatically.
6. **ALWAYS run `python3 -m unittest discover -s tests` before any update or deploy, and never ship red.**
7. Rules: correctness is decided by code, plain text only, safety, no data beyond the minimum.
8. The verbatim texts and keyboards from §4.
9. Legacy `relay/`: kept, but never run it at the same time as the engine on the same token (only one getUpdates consumer).

### SKILL.md
Same content condensed. The frontmatter description mentions: tutor bot programming cycle, a new subject means a new module in the one bot, run, codes, owner commands, tests-first. A request for "a bot for subject X" means adding a module to the single engine. A separate token (`BOT=<name>`) is used only if Alan explicitly asks for a separate bot.

### README.md (Russian, ≤ 25 lines)
Setup (`.env` keys), run, codes, owner commands, tests.

### Config files
- `.gitignore`: add `data/`.
- `.env.example`: add `TUTOR_OWNER_ID=`, `ANTHROPIC_API_KEY=`, `TUTOR_MODEL=claude-haiku-5-5`, `TUTOR_DB=`, `TUTOR_LLM_DAILY_LIMIT=40`.

---

## 8. Risks

1. **Answer extraction from free-form working** can misjudge ("wrong" when it is really "unparsed"). Mitigations: the unparsed path, the last-line rule, and recorded attempts visible in `/student`. Real student phrasing will need follow-up tuning.
2. **Self-consistency is not truth.** Property tests prove `display` passes `check`, not that the maths is right. Spot-check every skill with `python3 -m tutor sample` before launch; this needs a human or reviewer pass.
3. **Keyword safety detection is not real safeguarding.** It will miss things and give false positives. The owner must act on alerts; the bot only redirects to trusted adults and emergency services.
4. **Children's data and a third-party LLM** (UK GDPR / Age Appropriate Design Code). The LLM is off unless a key is set; only problem and message text are sent, with no names or ids.
5. **The model id `claude-haiku-5-5` is not confirmed** to exist. A wrong id silently disables the LLM; `--check` reveals this.
6. **"24/7" needs hosting**, which is out of scope. Until the process runs on an always-on machine, the bot is offline. Running `relay/listen.py` and the engine together on the same token causes 409 conflicts.
7. **Codes can be shared:** a code is one-time, but once redeemed the access stays with that Telegram chat until the owner runs `/reset`.

## 9. Open questions for the owner

1. ~~/start for verified students~~ — decided: resume without a new code.
2. Should students already verified through the old relay, and unused codes in `relay/.codes`, be migrated? Currently no: everyone gets a fresh code.
3. Should `/delete_my_data` also delete safety flags about that student? Currently yes, everything is deleted.
4. Should students (and parents) see a one-line privacy notice after the code (what is stored, `/delete_my_data`), and should the LLM (sending messages to Anthropic) be switched on at all for children?
5. Where will it run 24/7 (VPS, home PC, Replit)? This sets the next step after v1.

### Critical files for implementation
- /home/claude/claudemaxalan/tutor/content/base.py
- /home/claude/claudemaxalan/tutor/content/checker.py
- /home/claude/claudemaxalan/tutor/engine.py
- /home/claude/claudemaxalan/tutor/db.py
- /home/claude/claudemaxalan/tutor/subjects/maths.py
