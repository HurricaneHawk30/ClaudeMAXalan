# Tutor Engine v2 (addendum): every GCSE subject, marked by code only

*This is an addendum to `docs/ARCHITECTURE.md` (v1). Everything in v1 still applies unless a section below says it **replaces** or **adds** something. If the code and this document disagree, this document wins. If a contract turns out to be impossible, stop and report it rather than changing it quietly. Python 3.10+, standard library only.*

---

## 0. Scope and decisions

**What v2 includes**
- 33 new subjects for Years 10–11. Together with Maths (Years 7–11, unchanged) and Physics (Years 10–11, unchanged), the one bot covers 35 subjects.
- Two new answer kinds, both marked by code: `choice` and `short`.
- JSON banks in `tutor/subjects/banks/` load automatically. JSON "packs" in `tutor/subjects/packs/` let a Python subject module mix generator skills with bank skills.
- Repeat avoidance: DB schema v2 adds a `seen` table.
- Rubric items as "extended practice", with a model answer and no marking.
- New CLI command `python3 -m tutor audit` for content self-checks.

**What v2 does not include**
- LLM marking (off by default; owner decision).
- Years 1–9 for the new subjects.
- Images, audio, maps and diagrams.
- Coursework and NEA.
- Quotations from copyrighted set texts.
- Separate bots and hosting.

**Decisions**

| # | Decision |
|---|---|
| D1 | Correctness is decided by code only. The LLM may mark rubric items only when `TUTOR_LLM_MARKING=1` AND an API key is set. The default is off. LLM hints and feedback stay as in v1 (optional; off without a key). |
| D2 | **Rubric items are kept, under tight limits.** GCSE essay subjects are mostly extended writing, and comparing your own answer with a model answer is useful practice that costs nothing. The risks (a run of essays in a row, no progress signal) are contained: at most 15% of a skill, levels 4–5 only, never two in a row, no level change, no attempt recorded, and only in the subjects listed in §5. Every rubric item keeps `mark_scheme` and `max_marks`, so auto-marking later is a config switch, not a content rewrite. |
| D3 | Subject order: core subjects first (Maths, English, the three sciences), then the owner's groups (§4). |
| D4 | A topic has at most one bank skill and at most one generator skill, except all-generator topics. After a correct answer the engine switches skill, so a mixed topic alternates between practice questions and calculations. |
| D5 | Typo tolerance applies only to `short` answers with form `any` that are letters only and at least 6 characters long, with the same first letter. Rejected terms and an automatic list of similar words from the same file (§2.4) stop it from accepting a different term. |
| D6 | Repeat avoidance lives in the engine and works for every skill. Banks pick question `seed % n`, so consecutive seeds go through every question at a level. |
| D7 | A broken content file never stops the bot (loading is non-strict at runtime), but it always fails the tests (strict loading). |
| D8 | `tutor/subjects/maths.py` and `tutor/subjects/physics.py` are frozen. Nobody edits them. |

---

## 1. Who owns which files (no overlaps)

| Agent | Files (create or modify only these) |
|---|---|
| **engine-dev** | `tutor/content/{base,words,kinds,checker,bank,registry,audit,fmt,mathexpr,__init__}.py`; `tutor/{engine,texts,db,config,llm,intents,owner,messages,telegram,__main__,__init__}.py`; `tutor/subjects/__init__.py`; `CLAUDE.md` (only the sections listed in §3.6); `.claude/skills/tutor-bot-programming-cycle/SKILL.md`; `README.md`; `.env.example` |
| **content-1 STEM** | `tutor/subjects/{further_maths,stats,biology,chemistry,computer_science,astronomy}.py`, `tutor/subjects/_stem.py` (optional private helpers), `tutor/subjects/packs/{statistics,biology,chemistry,computer_science,astronomy}.json` |
| **content-2 English & performance** | `tutor/subjects/banks/{english_language,english_literature,drama,media_studies,film_studies}.json` |
| **content-3 Humanities** | `tutor/subjects/banks/{history,religious_studies,citizenship,classical_civilisation}.json`, `tutor/subjects/geography.py`, `tutor/subjects/packs/geography.json` |
| **content-4 Social & business** | `tutor/subjects/{psychology,economics,business}.py`, `tutor/subjects/_social.py` (optional), `tutor/subjects/packs/{psychology,economics,business}.json`, `tutor/subjects/banks/sociology.json` |
| **content-5 Languages** | `tutor/subjects/banks/{french,spanish,german,italian,russian,latin,arabic,mandarin}.json`. The lead may split this agent into 5a (French, Spanish, German, Italian) and 5b (Russian, Latin, Arabic, Mandarin); the files do not overlap. |
| **content-6 Creative & practical** | `tutor/subjects/banks/{music,design_technology,food_nutrition,pe,art_design}.json` |
| **test-dev** | `tests/**` (file list in §7) |
| **nobody** | `tutor/subjects/maths.py`, `tutor/subjects/physics.py`, `bot.py`, `relay/`, `docs/*.md`, `.claude/agents/*` |

**Rules**
- `banks/` and `packs/` never contain `.py` files or `__init__.py`. Whoever writes the first file creates the folder.
- Content agents never edit engine files. If they need an engine change, they report it.
- engine-dev never writes subject content or test fixtures.
- Content Python modules import only the `tutor.content` exports (§2.8), `tutor.content.fmt` (read-only), the standard library and their own `_*.py` helper.
- The Statistics module is called `stats.py` so it does not shadow the standard-library `statistics` module. Its subject id is still `statistics`.

**Build order**
1. **engine-dev, phase A** (content engine first): `base` → `words` → `kinds` → `checker` → `bank` → `registry` → `audit` + the CLI `audit` command. Report when it is done.
2. **Content agents** start straight away, writing against §2.4, §5 and §6. Once phase A has landed, they validate with `python3 -m tutor audit --file PATH` (one file) or `--subject ID`.
3. **engine-dev, phase B**: db, engine, texts, config, llm, intents, docs.
4. **test-dev** writes tests from this document in parallel, then runs them against the code. It reports failures and does not fix implementation or content.
5. **The lead** integrates: runs the default and full test runs, and sends failures back to the owning agent.

---

## 2. Content engine contracts (engine-dev implements; content and tests consume)

### 2.1 `tutor/content/base.py` (additions)

```python
ANSWER_KINDS = ("number", "fraction", "set", "assign", "expr", "ratio", "rubric", "choice", "short")
CHOICE_LETTERS = "ABCDE"
SHORT_FORMS = ("any", "strict", "case", "pinyin")

# Answer: fields unchanged. New value shapes:
#   choice: value = {"options": list[str] (displayed order, 3..5), "correct": int}; form "any";
#           display = f"{CHOICE_LETTERS[correct]}) {options[correct]}"        e.g. "B) Mitochondria"
#   short:  value = {"accept": list[str] (>= 1), "reject": list[str]}; form in SHORT_FORMS;
#           display = accept[0]

@dataclass(frozen=True)
class Problem:            # v1 fields unchanged, plus at the end:
    ref: str = ""         # stable id of the underlying question: "<skill_id>#<question id>" for bank items, "" = none

@dataclass(frozen=True)
class BankItem:
    ref: str                              # "<skill_id>#<question id>", unique across the registry
    level: int                            # level written in the file, 1..5
    kind: str                             # answer kind
    render: Callable[[int], Problem]      # seed -> Problem(level=self.level, seed=seed, ref=self.ref); pure; choice options shuffled by seed

@dataclass(frozen=True)
class Skill:              # v1 fields unchanged, plus at the end:
    items: tuple[BankItem, ...] = ()      # bank skills: every question; generator skills: ()

def fingerprint(p: Problem) -> str
    # p.ref if p.ref else "t:" + sha1(" ".join(p.text.split()).casefold().encode()).hexdigest()[:16]
```

- `problem_to_json` writes `"ref"`. `problem_from_json` reads `d.get("ref", "")`, so v1 pending rows still load.

### 2.2 `tutor/content/kinds.py` (new)

```python
def shuffle_order(n: int, seed: int) -> list[int]
    # order = list(range(n)); random.Random(f"choice:{seed}").shuffle(order); return order
def letters_text(n: int) -> str            # 3 -> "A, B or C"; 4 -> "A, B, C or D"; 5 -> "A, B, C, D or E"
def build_choice(stem: str, options: Sequence[str], correct: int, seed: int,
                 feedback: Sequence[str | None] | None = None) -> tuple[str, Answer, tuple[Mistake, ...]]
def build_short(accept: Sequence[str], reject: Sequence[str] = (), form: str = "any",
                feedback: Mapping[str, str] | None = None) -> tuple[Answer, tuple[Mistake, ...]]
```

**`build_choice`**
- `order = shuffle_order(n, seed)`; `shown = [options[i] for i in order]`; `c = order.index(correct)`.
- Text: `stem.rstrip() + "\n\n" + "\n".join(f"{L}) {opt}" for L, opt in zip(CHOICE_LETTERS, shown))`.
- Answer: `Answer("choice", f"{CHOICE_LETTERS[c]}) {shown[c]}", {"options": shown, "correct": c})`.
- Mistakes: for each displayed wrong option `j` whose feedback is set, `Mistake(Answer("choice", f"{L_j}) {shown[j]}", {"options": shown, "correct": j}), fb)`.
- Raises `ValueError` on any input that breaks §2.4 rule 7.

**`build_short`**
- Answer: `Answer("short", accept[0], {"accept": list(accept), "reject": list(reject)}, form=form)`.
- Mistakes: for each `r` in reject that has feedback, `Mistake(Answer("short", r, {"accept": [r], "reject": []}, form=form), fb)`.
- Raises `ValueError` on any input that breaks §2.4 rule 8.

`tutor/content/words.py` (new, internal): normalisation, folding and the restricted Damerau–Levenshtein (optimal string alignment, "OSA") distance used below. The tests exercise it only through `check`.

### 2.3 `tutor/content/checker.py`: `choice` and `short` (adds to v1 §2.3)

```python
NOTE_SPELLING = "Watch the spelling: {answer}"
NOTE_ACCENTS  = "Watch the accents: {answer}"
FORM_CASE     = "Check your capital letters — in symbols and formulae they change the meaning"
```

**Verdict change:** a `correct` verdict may now carry `feedback` = a note (NOTE_SPELLING or NOTE_ACCENTS, filled with the matched accepted answer as written). Displays and exact answers never get a note. v1 kinds never return a note.

**Shared answer-line preparation** (choice and short)
1. Apply the v1 text normalisation, then NFC. Map `’‘` → `'` and `“”` → `"`. Subscript and superscript digits become digits (`CO₂` → `CO2`); `⁺⁻` become `+-`.
2. Split the text into non-empty lines.
   - Ignore any line that starts with a reason word (`because`, `since`, `coz`, `cuz`, `as`, `this is because`, `that's because`) or a v1 check word.
   - In the other lines, cut from the first `because` / `coz` / `cuz` / `since` / `check` / `checking` onwards when text remains before it.
3. Strip leading filler phrases from each line, repeatedly. They are case-insensitive, whole words, and longest are tried first:
   - common: `answer:`, `answer -`, `answer`, `ans:`, `final answer`, `my answer is`, `the answer is`, `answer is`, `i think it's`, `i think its`, `i think it is`, `i think it was`, `i think`, `i believe`, `i guess`, `i'd say`, `i would say`, `it's called`, `its called`, `it is called`, `this is called`, `the word is`, `the term is`, `known as`, `it's`, `its`, `it is`, `it was`, `is it`, `it must be`, `must be`, `probably`, `maybe`, `definitely`, `actually`;
   - choice only: `option`, `letter`, `i choose`, `i pick`, `i'll go with`, `going with`.
4. Strip trailing junk as in v1 (`.,;!?`, ticks, emoji, smileys, `lol`, `please`). Then remove one pair of wrapping quotes or brackets.

**`norm_f(x)`: normalisation by short-answer form**

| Form | Rule |
|---|---|
| `any` | casefold; remove punctuation except inside numbers (decimal point, `/` between digits, `-` before a digit); `-` and `/` between letters → space; delete apostrophes; collapse spaces; strip one leading `the ` / `a ` / `an ` if text remains |
| `strict` | as `any` but no article stripping; then remove all spaces (a spaced copy is kept for counting words and for step 7) |
| `case` | no casefolding; remove all whitespace and `. , ; : ! ? " '`; keep `+ - ( )` |
| `pinyin` | casefold; fold tone marks (`ǚ` → `u`); delete digits 1–5 that follow a letter; remove spaces, apostrophes and hyphens; never adds a note |

**`fold` (forms `any` and `strict`)** compares two variants of every accepted answer:
- plain variant: NFKD, then drop combining marks on Latin letters only; `ß→ss`, `æ→ae`, `œ→oe`, `ø→o`, `ł→l`;
- German variant: first `ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, then fold as above.

In every form, `ё→е` is applied with no note. Cyrillic `й`, Arabic and CJK are never folded.

**choice** (n = number of options; valid letters = `CHOICE_LETTERS[:n]`)

Each prepared line, read from the bottom up, names one of: a letter, "conflict", "invalid", or nothing.
- (a) The line matches `^\(?([A-Ea-e])\)?[.:]?$`. That letter is named; a letter beyond n is "invalid".
- (b) The line matches `^([A-Ea-e])\s*([).:\-–])\s*(.+)$`. Compare the rest R (normalised with `any`, then folded) with the options:
  - R equals that letter's option, or R matches no option → the letter;
  - R equals a different option → "conflict".
- (b′) The line matches `^([A-Ea-e])\s+(.+)$` and R equals that same letter's option → the letter. Otherwise go to (c).
- (c) The whole line, normalised with `any` and folded, equals exactly one option's normalised text → that option's letter.
- Otherwise the line names nothing.

Verdict:
- any "conflict" or "invalid" line → `unparsed`;
- exactly one distinct letter named → `correct` if it is the right letter, otherwise `wrong`;
- no letter, or two or more distinct letters → `unparsed`.

There is no typo tolerance, and choice never returns a note.

**short** (A = normalised accepted answers; R = normalised rejected answers)

The answer line is the bottom-most prepared line that contains a letter or a digit. If there is none, the verdict is `unparsed`.
1. `t = norm_f(line)`. If t is empty → `unparsed`.
2. **Numeric answers.** If every accepted answer is digits only (a year, for example):
   - take the digit tokens in t as strings;
   - correct if an accepted string is among them and no other token has 3 or more digits;
   - any other case with tokens → `wrong`;
   - no digits at all → go to step 8.
3. t ∈ A → `correct`.
4. t ∈ R → `wrong`.
5. Folding and case:
   - forms `any` / `strict`: fold(t) equals a folded accept → `correct` + NOTE_ACCENTS; fold(t) equals a folded reject → `wrong`;
   - form `case`: casefold(t) equals casefold of an accept → `wrong` + FORM_CASE.
6. **Typo tolerance** (form `any` only). Eligible accepts are normalised accepts made of letters and spaces only, with length ≥ 6 and at most 3 words. A typo is accepted when all of these hold:
   - t is letters and spaces only;
   - `t[0] == a[0]`;
   - `osa(t, a) ≤ 1` (≤ 2 when `len(a) ≥ 10`);
   - that distance is strictly smaller than t's distance to every reject.

   Then → `correct` + NOTE_SPELLING with that accept.
7. **Containment** (forms `any` / `strict`, using the spaced copy). An accept of 3 or more characters occurs in t as whole words:
   - if every remaining word is in FILLER_WORDS → `correct` (+ NOTE_ACCENTS if it matched only after folding);
   - otherwise → `unparsed`.
8. The line is a question: it ended with `?` before cleaning, or its first word is one of `what why how can could explain tell which who where when does do` → `unparsed`.
9. The word count of t is more than `max(6, 2 × the longest accept's word count)` → `unparsed`.
10. Otherwise → `wrong`.

FILLER_WORDS = `the a an it its is was are were be called named known as this that process word term answer i think believe guess would say they of my final probably maybe definitely type kind example`.

The v1 mistake loop is unchanged: when the verdict is `wrong` with no feedback, the first mistake whose answer `check`s as `correct` supplies the feedback.

**Acceptance table: choice.** Options as displayed are `["Nucleus", "Mitochondria", "Ribosome", "Cell membrane"]`, correct = 1, display `B) Mitochondria`, and option A has a mistake with feedback fbA. test-dev asserts every row exactly.

| Verdict | Inputs |
|---|---|
| C | `B`, `b`, `(b)`, `B)`, `b.`, `[B]`, `B!`, `B ✅`, `answer: B`, `Answer - b`, `the answer is B`, `it's B`, `I think it's b`, `option B`, `B) Mitochondria`, `b - mitochondria`, `B mitochondria`, `Mitochondria`, `the mitochondria`, `MITOCHONDRIA`, `B because it releases energy`, `I think it's\nB`, `B\nbecause that's where respiration happens` |
| W | `A` (fbA), `a` (fbA), `Nucleus` (fbA), `A) Nucleus` (fbA), `(c)`, `answer: D`, `cell membrane` |
| U | `` (empty), `E`, `B or C`, `B and C`, `B, C`, `B/C`, `B) Nucleus`, `B\nactually C`, `mitochondrion`, `2`, `what is a ribosome?` |

**Acceptance table: short.** C = correct, W = wrong, WF = wrong with the named feedback, U = unparsed.

| Answer | C | C + note | W / WF | U |
|---|---|---|---|---|
| any; accept `["photosynthesis"]`, reject `["respiration"]` (feedback fbR) | `photosynthesis`, `Photosynthesis.`, `PHOTOSYNTHESIS`, `it's photosynthesis`, `the answer is photosynthesis`, `answer: photosynthesis`, `I think it's photosynthesis`, `it's called photosynthesis`, `photosynthesis because light is absorbed`, `"photosynthesis"`, `photosynthesis 😊` | NOTE_SPELLING("photosynthesis"): `photosinthesis`, `photosynthesys` | W `chlorophyll`, `glucose`, `fotosynthesis`; WF fbR: `respiration`, `Respiration.` | ``, `what does photosynthesis mean?`, `photosynthesis and respiration`, `the plant uses light energy from the sun to make its own food`, `can you explain` |
| any; accept `["alkane"]`, reject `["alkene"]` | `alkane`, `an alkane` | NOTE_SPELLING("alkane"): `alkanes`, `alkaen` | W `alkene` | — |
| strict; accept `["la bibliothèque"]`, reject `["la librairie", "le bibliothèque"]` with feedback fbL / fbG | `la bibliothèque`, `La Bibliothèque`, `la bibliothèque.` | NOTE_ACCENTS("la bibliothèque"): `la bibliotheque`, `LA BIBLIOTHEQUE` | WF fbL: `la librairie`; WF fbG: `le bibliothèque`, `le bibliotheque`; W `bibliothèque`, `la bibliotek` | ``, `c'est la bibliothèque` |
| strict; accept `["das Mädchen"]` | `das Mädchen`, `Das Mädchen` | NOTE_ACCENTS("das Mädchen"): `das Madchen`, `das Maedchen` | W `die Mädchen`, `Mädchen` | — |
| case; accept `["CO2"]` | `CO2`, `CO₂`, `C O 2` | — | WF FORM_CASE: `co2`, `Co2`; W `CO`, `O2` | `` |
| pinyin; accept `["nǐ hǎo"]` | `nǐ hǎo`, `ni hao`, `nihao`, `ni3 hao3`, `Ni Hao` | — | W `zai jian`, `xie xie` | `` |
| any; accept `["1918"]` | `1918`, `in 1918`, `It ended in 1918.`, `11 November 1918` | — | W `1917`, `1919`, `1914-1918` | `` |
| any; accept `["00101101", "0010 1101"]` | `00101101`, `0010 1101` | — | W `101101`, `00101100` | `` |

### 2.4 `tutor/content/bank.py`: bank format v2 (replaces v1 §2.5 "not auto-loaded")

```python
class BankError(ValueError): ...
BANKS_DIR: str   # <tutor>/subjects/banks
PACKS_DIR: str   # <tutor>/subjects/packs
def load_bank(path: str) -> tuple[Subject, list[Skill]]          # complete subject file; cached by (realpath, mtime_ns, size)
def register_bank(reg: Registry, path: str) -> None
def load_pack(name_or_path: str, subject_id: str) -> list[Skill]   # "biology" -> PACKS_DIR/biology.json; cached the same way
```

**Bank file** (`banks/<subject_id>.json`, auto-loaded):

```json
{
  "subject": {"id": "history", "title": "History", "order": 30},
  "skills": [
    {"id": "history.germany", "title": "Germany 1890–1945",
     "aliases": ["nazi germany", "weimar", "germany", "hyperinflation"],
     "questions": [
       {"id": "g01", "level": 1, "text": "In which year did Hitler become Chancellor of Germany? Give the year.",
        "short": {"accept": ["1933"]},
        "solution": "President Hindenburg appointed Hitler Chancellor in January 1933",
        "hint": "It was the same year as the Reichstag Fire"},
       {"id": "g02", "level": 2, "topic_note": "Weimar Republic",
        "text": "Which treaty did Germany sign in 1919 at the end of the First World War?",
        "choice": {"options": ["Treaty of Versailles", "Treaty of Brest-Litovsk", "Locarno Treaties", "Treaty of Rome"],
                   "correct": 0,
                   "feedback": [null, "Brest-Litovsk (1918) ended the war between Germany and Russia", null,
                                "The Treaty of Rome (1957) set up the European Economic Community"]},
        "solution": "Germany signed the Treaty of Versailles in June 1919",
        "hint": "It was signed in a famous palace near Paris"},
       {"id": "g29", "level": 5, "text": "Explain one reason why support for the Nazis grew between 1929 and 1932.",
        "rubric": {"model_answer": "…", "mark_scheme": "…", "max_marks": 4},
        "solution": "…", "hint": "…"}
     ]}
  ],
  "years": {"10,11": {"rows": [[{"id": "history.y{year}.germany", "label": "Germany 1890–1945", "skills": ["history.germany"]},
                                 {"id": "history.y{year}.elizabethan", "label": "Elizabethan England", "skills": ["history.elizabethan"]}]]}}
}
```

**Pack file** (`packs/<subject_id>.json`, never auto-loaded): `{"subject_id": "chemistry", "skills": [ …skill objects… ]}`.

- **Question keys:** `id`, `level`, `text`, `topic_note`, `solution`, `hint`, and exactly one of `answer` (v1 kinds; may have `mistakes`), `choice`, `short` or `rubric`.
- **Rendering:**
  - `topic_note` → the text starts with `[{topic_note}] `;
  - `choice` → `build_choice(stem, options, correct, seed, feedback)`;
  - `short` → `build_short(...)`, plus auto-rejects (below);
  - `rubric` → `Answer("rubric", display=model_answer, mark_scheme=…, max_marks=…)`.
- **Ref:** `ref = f"{skill_id}#{question id}"`. If a question has no id, `#<index>` is used (v1 fixtures only).
- **Selection:** `generate(level, seed)` takes the questions of the nearest level that has any (ties prefer the lower level), in file order, picks `item = items[seed % len(items)]` and returns `replace(item.render(seed), level=level)`. `Skill.items` = all items in file order.
- **Auto-rejects (stop near-miss terms):** for each `short` item with form `any` and typo-eligible accepts (§2.3 step 6), add to `value["reject"]` (at most 20) every term of the file's vocabulary that is ALL of the following:
  - not an accept of this item;
  - letters and spaces only;
  - starts with the same first letter as an accept;
  - within 2 characters of the accept's length;
  - at OSA distance ≤ 2 from that accept;
  - not a plural variant of an accept (accept + `s` / `es`).

  The file's vocabulary = every normalised short accept and every choice option text in that file.
- **Cleaning:** the loader strips trailing `.` from `solution`, `hint` and every feedback string, and lowercases aliases.
- **Years:** a year key may be `"10"` or a comma list such as `"10,11"`. `{year}` in topic ids is replaced for each year.

**Validation.** Every failure raises `BankError` with the JSON path in the message.
1. Unknown keys at any level (subject, skill, question, `choice`, `short`, `rubric`, year, topic) → error.
2. A question needs exactly one of `answer` / `choice` / `short` / `rubric`. `answer.kind` of `choice` or `short` → error ("use the choice/short key").
3. `id` matches `^[A-Za-z0-9_-]{1,24}$` and is unique within the skill. `level` is an int in 1..5.
4. `text`, `solution` and `hint` are non-empty. `solution` ≤ 300 chars. Rendered text (with the note and options) ≤ 600 chars. `topic_note` ≤ 40 chars with no newline.
5. No duplicate stems within a skill. Stems are compared casefolded, with punctuation removed and whitespace collapsed; `topic_note` is ignored.
6. Skill: at least one question, a non-empty title, and a non-empty list of non-empty aliases.
7. **choice:**
   - 3–5 options, each 1–120 chars, with no newline;
   - no duplicates after `any` normalisation + folding;
   - `correct` is an int in range;
   - `feedback` is optional; if present it has the same length as `options`, its entries are null or non-empty strings, and `feedback[correct]` is null;
   - no option matches `\b(all|none|both|neither) of (the )?(above|these)\b`, `\b[A-E]\s*(and|or|&|,)\s*[A-E]\b`, `^\(?[A-Ea-e]\)?$`, or starts with `^[A-E][).:]\s`;
   - checked on the seed-0 render: the display is `correct` with no note, and every other letter is `wrong`.
8. **short:**
   - `accept` is a non-empty list of 1–80 char strings, each non-empty after normalisation (duplicates after normalisation are allowed; the first one stays the display);
   - `reject` is a list of strings; none may equal an accept after normalisation, or after folding for `any` / `strict`;
   - `form` ∈ SHORT_FORMS;
   - `feedback` keys must be in `reject`; values are non-empty strings;
   - the display is `correct` with no note, and every reject is `wrong`.
9. **rubric:** `model_answer` 1–600 chars, `mark_scheme` 1–600 chars, `max_marks` int 1–12.
10. **answer (v1 kinds):** v1 rules apply. The display must be judged `correct`; mistakes are judged `correct` for themselves and are dropped when they coincide with the answer.
11. The hint must not contain, case-insensitive and as whole words, any of: the display (≥ 3 chars), the correct option text (≥ 4 chars), or an accept (≥ 4 chars).
12. Pack: `subject_id` matches the argument, and every skill id starts with `subject_id + "."`.

### 2.5 `tutor/content/registry.py` (changes)

- `load_registry(banks: Iterable[str] = (), strict: bool = True) -> Registry`. Loading order:
  1. modules in `tutor.subjects`, by name, skipping `_*`;
  2. `BANKS_DIR/*.json`, sorted by file name, skipping `_*`;
  3. the extra `banks`.
- `strict=False`: a source that raises any exception is logged (`subject source <name> failed: <type>: <message>`) and skipped. Failures are collected in `reg.load_errors: list[str]`. `Engine(registry=None)` uses `strict=False`; tests, `sample` and `audit` use strict.
- `RESERVED_LABELS` adds `"A"`, `"B"`, `"C"`, `"D"`, `"E"`.
- Label matching (`_norm_label`) also folds `–` and `—` to `-`, so `germany 1890-1945` finds `Germany 1890–1945`.
- Alias matching (`_norm_text`) also folds Latin diacritics, so `passe compose` finds an alias `passé composé`.

### 2.6 `tutor/content/audit.py` + CLI

| Command | What it checks |
|---|---|
| `python3 -m tutor audit` | every source, each loaded on its own; one broken file never hides the others |
| `python3 -m tutor audit --subject ID` | only the source that registers subject ID |
| `python3 -m tutor audit --file PATH` | one bank file (has `subject`) or pack file (has `subject_id`); rules that need labels are skipped |

- Output, one line per skill: `{skill_id}: bank|gen items={n} L1-5={a}/{b}/{c}/{d}/{e} choice={x}% short={y}% rubric={z}%`. Problems follow as `  ERROR: …` lines and audit-only warnings as `  WARN: …` lines.
- Exit 0 when there are no ERRORs, 1 otherwise.
- Checks: everything in §2.4, the lint rules L1–L11 (§7), and a generator smoke test (20 seeds × 5 levels: deterministic, display correct, lengths).
- `--check` also prints `Subjects: {n} loaded` and one line per failed source.

### 2.7 `fmt.py`

Unchanged. Content modules may call `fmt.build(...)` with choice or short answers. To set a ref, use `dataclasses.replace(problem, ref=...)`.

### 2.8 `tutor/content/__init__.py` exports (adds)

`BankItem, fingerprint, CHOICE_LETTERS, SHORT_FORMS, build_choice, build_short, shuffle_order, letters_text, load_pack, BANKS_DIR, PACKS_DIR, NOTE_SPELLING, NOTE_ACCENTS, FORM_CASE`

---

## 3. Core contracts (engine-dev, phase B)

### 3.1 New texts and keyboards (`tutor/texts.py`, verbatim; adds to v1 §4)

```
PROBLEM_CHOICE      = "Problem {n}: {text}\n\nReply with the letter of your answer — tap a button below 😊"
PROBLEM_CHOICE_EXAM = "Problem {n} (1 mark): {text}\n\nReply with the letter of your answer — tap a button below 😊"
PROBLEM_SHORT       = "Problem {n}: {text}\n\nSend me your answer — just the word or short phrase 😊"
PROBLEM_SHORT_EXAM  = "Problem {n} (1 mark): {text}\n\nSend me your answer — just the word or short phrase 😊"
PROBLEM_RUBRIC      = "Problem {n} (extended practice, {marks} mark{s}): {text}\n\nWrite your answer, then I'll show you a model answer to compare with yours 😊"
CORRECT_NOTE        = "✅ Correct! {solution}. {note}"
CHOICE_UNPARSED     = "🤔 Please reply with just one letter: {letters}. Or type «hint» for a hint, or «skip» to see the solution."
SHORT_UNPARSED      = "🤔 I couldn't find one clear answer in that. Send just the word or short phrase — or type «hint» for a hint, or «skip» to see the solution."
WHY_FACT            = "Here's why: {solution}"
```

- In PROBLEM_RUBRIC, `marks` = `answer.max_marks` and `s` = `""` when marks == 1.
- In CHOICE_UNPARSED, `letters = letters_text(n)`.
- `choice_kb(n, rows) = (tuple(CHOICE_LETTERS[:n]),) + topic_kb(rows)`: the letter row sits on top of the usual lesson keyboard.
- `subject_kb` is unchanged: registry order, 2 per row, then `(CHANGE_YEAR,)` (§4).

### 3.2 `tutor/engine.py` (changes to v1 §3.7)

**Choosing the next problem (repeat avoidance).** `_next_problem(st, topic, skill_id, level, number, prev: Problem | None)`:

```
REROLL_TRIES = 40
recent = store.recent_seen(chat, skill_id)            # fingerprints, newest first, at most 30
base = rng.randrange(1, 2**31 - REROLL_TRIES)
for k in 0..REROLL_TRIES-1:  seed = base + k;  p = skill.generate(gen, seed)
    skip p if prev and (fingerprint(p) == fingerprint(prev) or p.text == prev.text)
    skip p if prev and prev.answer.kind == "rubric" and p.answer.kind == "rubric"
    take the first p whose fingerprint is not in recent
if none taken: use the non-skipped candidate whose fingerprint is OLDEST in recent (largest index; ties -> first)
if every candidate was skipped: p = skill.generate(gen, base)    # last resort; may repeat
store.add_seen(chat, skill_id, fingerprint(p)); set_pending(seed=chosen seed)
```

**Problem message by kind**
- choice → PROBLEM_CHOICE, or PROBLEM_CHOICE_EXAM on a past-paper topic;
- short → PROBLEM_SHORT / PROBLEM_SHORT_EXAM;
- rubric → PROBLEM_RUBRIC (exam or not);
- other kinds → v1 (PROBLEM / PROBLEM_EXAM with `EXAM_MARKS[gen]`).

**Keyboards**
- `lesson_kb(st, problem)` = `choice_kb(n, rows)` when `problem.answer.kind == "choice"`, otherwise `topic_kb(rows)`.
- In the lesson step, `current_kb(st)` uses the pending problem, so DISTRESS, CHEAT, TEXT_ONLY, HINT and the unparsed replies keep the letter row while a choice problem is open.
- The v1 invariant still holds.

**Marking**
- `correct` with feedback → CORRECT_NOTE(solution, note). Otherwise the v1 rules apply (level up, other skill).
- `wrong` → `why` = the verdict's feedback, else the LLM feedback, else WHY_FACT(solution) for choice/short and WHY_FALLBACK(solution) for other kinds.
- `unparsed` → the LLM chat if allowed (as v1); else CHOICE_UNPARSED (choice), SHORT_UNPARSED (short), or v1 UNPARSED / OFFTOPIC.
- `rubric` → `mark_rubric` only if `config.llm_marking` and the LLM is allowed. Otherwise UNMARKABLE and the next problem (same skill and level, no attempt recorded), as v1.
- Every call site passes `prev = p.problem` (None from `start_topic`).

### 3.3 `tutor/db.py`: schema v2 (adds to v1 §3.3)

```sql
CREATE TABLE IF NOT EXISTS seen (
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, skill TEXT NOT NULL, fp TEXT NOT NULL,
  UNIQUE (chat_id, skill, fp));
CREATE INDEX IF NOT EXISTS seen_chat_skill ON seen (chat_id, skill, id);
```

```python
SEEN_KEEP = 30
def recent_seen(self, chat_id: int, skill: str, limit: int = SEEN_KEEP) -> list[str]   # newest first (id desc)
def add_seen(self, chat_id: int, skill: str, fp: str, keep: int = SEEN_KEEP) -> None
    # INSERT OR REPLACE (re-inserts as newest), then delete all but the newest `keep` rows for (chat, skill)
```

- **Migration** (in `__init__`, after the schema script): `INSERT OR IGNORE meta('schema_version','2')`, then `UPDATE meta SET value='2' WHERE key='schema_version' AND value='1'`. A version above 2 → log a warning and continue. No ALTERs are needed.
- `delete_student_data` also deletes the chat's `seen` rows.

### 3.4 Config, LLM, intents

- **Config:** `llm_marking: bool = False`. It is True when `TUTOR_LLM_MARKING` is `1`, `true`, `yes` or `on` (case-insensitive).
- **`llm.leaks_answer`:**
  - choice → True if the correct option text (≥ 3 chars) occurs casefolded, or the text matches `\b(option|answer|letter|choice)\s*\(?{L}\b` or `\b{L}\)` for the correct letter L. The v1 value test is skipped for choice.
  - short → True if any accept (normalised, ≥ 3 chars) occurs as whole words in the normalised text.
- **`intents._SKIP_EXACT`** adds `no clue`, `not sure`, `im not sure`, `i'm not sure`, `unsure` (exact matches only).

### 3.5 CLI

- `audit` as in §2.6.
- `sample` works for bank skills (prints the rendered text with its options, the answer and the ref).
- `--check` reports subject loading (§2.6).

### 3.6 Docs (engine-dev)

**CLAUDE.md**
- §2: add the row `TUTOR_LLM_MARKING` | "1 = the LLM marks extended-practice answers (costs money; default off)".
- §5: subjects are a JSON bank `tutor/subjects/banks/<id>.json` (auto-loaded) or a module `tutor/subjects/<name>.py` with an optional pack `tutor/subjects/packs/<id>.json`; check with `python3 -m tutor audit --subject <id>`; the spec is in `docs/ARCHITECTURE_V2.md`.
- §6: "30 seeds per generated skill, plus every bank question".
- §8: the §4 subject keyboard and the §3.1 texts.

**Other files**
- SKILL.md: the same changes, condensed.
- README.md (Russian): one line each on the subjects and `audit`.
- `.env.example`: add `TUTOR_LLM_MARKING=0`.

---

## 4. Subject list and keyboard

New subjects have Years 10 and 11 only, with the same rows in both years. Topic ids are `<subject_id>.y10.<slug>` and `<subject_id>.y11.<slug>`. Every topic uses `level_map (1,2,3,4,5)`; past paper uses `(2,3,3,4,5)`. Subject titles are at most 18 characters; topic labels for new subjects are at most 30.

| Order | Title | id | Source | Order | Title | id | Source |
|---|---|---|---|---|---|---|---|
| 10 | Maths | maths | frozen | 12 | English Language | english_language | bank |
| 14 | English Literature | english_literature | bank | 16 | Biology | biology | module + pack |
| 18 | Chemistry | chemistry | module + pack | 20 | Physics | physics | frozen |
| 22 | Further Maths | further_maths | module | 24 | Statistics | statistics | module `stats.py` + pack |
| 26 | Computer Science | computer_science | module + pack | 28 | Astronomy | astronomy | module + pack |
| 30 | History | history | bank | 32 | Geography | geography | module + pack |
| 34 | Religious Studies | religious_studies | bank | 36 | Citizenship | citizenship | bank |
| 38 | Classical Civ | classical_civilisation | bank | 40 | Psychology | psychology | module + pack |
| 42 | Sociology | sociology | bank | 44 | Economics | economics | module + pack |
| 46 | Business | business | module + pack | 48 | Media Studies | media_studies | bank |
| 50 | Film Studies | film_studies | bank | 52 | French | french | bank |
| 54 | Spanish | spanish | bank | 56 | German | german | bank |
| 58 | Italian | italian | bank | 60 | Russian | russian | bank |
| 62 | Latin | latin | bank | 64 | Arabic | arabic | bank |
| 66 | Mandarin Chinese | mandarin | bank | 68 | Music | music | bank |
| 70 | Drama | drama | bank | 72 | Design & Tech | design_technology | bank |
| 74 | Food & Nutrition | food_nutrition | bank | 76 | PE | pe | bank |
| 78 | Art & Design | art_design | bank | | | | |

```
Years 10/11 (rows of 2, registry order):
[Maths] [English Language] / [English Literature] [Biology] / [Chemistry] [Physics] / [Further Maths] [Statistics] /
[Computer Science] [Astronomy] / [History] [Geography] / [Religious Studies] [Citizenship] / [Classical Civ] [Psychology] /
[Sociology] [Economics] / [Business] [Media Studies] / [Film Studies] [French] / [Spanish] [German] / [Italian] [Russian] /
[Latin] [Arabic] / [Mandarin Chinese] [Music] / [Drama] [Design & Tech] / [Food & Nutrition] [PE] / [Art & Design] /
[🎓 Change year]
Years 7–9: [Maths] / [🎓 Change year]
```

---

## 5. Content specification

**Notation**
- `B` = bank skill: at least 30 questions, at least 4 at every level, written in a bank or pack file.
- `G` = generator skill: Python, v1 §5 generator rules apply.
- Rows are written `label (slug): skills | label (slug): skills / second row …`.
- After each skill: `"Title"` then aliases; the first alias must be unique within the subject.
- "Extras" are skills reachable only through «My own topic». Required extras must meet the same minimum as row skills; optional extras are wave 2.

**Difficulty ladder for banks**
- L1: recall a term or fact.
- L2: tell similar terms apart; recall in short-answer form.
- L3: apply to a simple new example.
- L4: two steps, or interpret short data or a short extract.
- L5: exam-style reasoning (best explanation, cause and consequence, which statement is accurate); rubric items where the subject allows them.

Aim for 6 questions per level.

**Mixes (bank skills)**

| Mix | Choice | Short | Rubric (levels 4–5) | Number |
|---|---|---|---|---|
| M1 | 55–70% | 20–35% | ≤ 15% | — |
| M2 | 55–75% | 25–45% | none | ≤ 15% |
| M3 (languages) | 40–60% | 40–60% | none | — |
| M4 (Arabic, Mandarin) | ≥ 65% | ≤ 35%, English or pinyin | none | — |

In every bank skill, choice + short must be at least 85% of the questions.

**Subjects that may use rubric items:** English Language, English Literature, History, Geography, Religious Studies, Citizenship, Classical Civ, Psychology, Sociology, Economics, Business, Media Studies, Film Studies, Drama.

### 5.1 content-1 (STEM)

**Further Maths** (`further_maths.py`, all G). Rows: `Algebra & functions` (algebra): functions, polynomials | `Coordinate geometry` (coordinates): coordinates / `Calculus` (calculus): calculus | `Matrices & trigonometry` (matrices_trig): matrices, trigonometry.

| Skill | Title | Aliases | Ladder L1 → L5 |
|---|---|---|---|
| `further_maths.functions` G | "Functions" | composite function, inverse function, functions, fg(x), domain | f(a) → fg(a) → f⁻¹(x) linear (expr) → fg(x) (expr `expanded`) → solve f(x)=g(x) (set) |
| `further_maths.polynomials` G | "Factor theorem & completing the square" | factor theorem, remainder theorem, completing the square, cubic, turning point | f(a) for a cubic → k such that (x−a) is a factor → (x+p)²+q (assign p, q) → turning point (assign x, y) → solve a cubic given one factor (set) |
| `further_maths.coordinates` G | "Coordinate geometry" | equation of a circle, coordinate geometry, midpoint, perpendicular gradient, distance between points | midpoint (assign x, y) → gradient (fraction) → perpendicular gradient (fraction) → distance (1 dp) → circle centre and radius from the general form (assign a, b, r) |
| `further_maths.calculus` G | "Differentiation" | differentiation, differentiate, dy/dx, stationary points, gradient function | d/dx kxⁿ (expr) → polynomial (expr) → gradient at a point (number) → stationary x-values (set) → stationary point (assign x, y) |
| `further_maths.matrices` G | "Matrices" | matrix multiplication, matrices, matrix, identity matrix, transformation matrix | entry of kA → entry of AB → image of a point (assign x, y) → name the transformation (choice, ref per transformation) → product matrix (assign a, b, c, d) |
| `further_maths.trigonometry` G | "Trigonometry" | exact trig values, trig equations, trig identities, sin cos tan | exact value (choice with surds, ref per value) → exact value (fraction) → solve sin/cos x = k for 0–360° (set, 1 dp) → tan x = k (set) → identities (fraction) |

**Statistics** (`stats.py` + `packs/statistics.json`). Rows: `Collecting data` (collecting): data_collection, stratified | `Averages & spread` (averages_spread): averages, spread / `Diagrams & correlation` (diagrams): diagrams, spearman | `Probability & index numbers` (probability): probability, index_numbers.

| Skill | Title | Aliases | Ladder or mix |
|---|---|---|---|
| `statistics.data_collection` B (M2) | "Collecting data & sampling" | sampling methods, sample, questionnaire, types of data, hypothesis, bias, census, pilot study | — |
| `statistics.stratified` G | "Stratified sampling" | stratified sample, capture recapture, petersen | stratum fraction (fraction `simplest`) → one stratum's sample → rounding → two strata (ordered set) → capture–recapture |
| `statistics.averages` G | "Averages" | estimated mean, mean, median, mode, averages, frequency table | mean → median (even count) → frequency-table mean → grouped estimated mean (1 dp) → missing value or combined mean |
| `statistics.spread` G | "Measures of spread" | interquartile range, range, iqr, quartiles, standard deviation, outlier | range → quartiles → IQR → outlier limits → standard deviation (2 dp, formula given in the question) |
| `statistics.diagrams` B (M2) | "Diagrams & correlation" | scatter diagram, correlation, line of best fit, histogram, box plot, interpolation, causation | — |
| `statistics.spearman` G | "Spearman's rank" | spearman's rank, spearman, rank correlation | rank a value → Σd² → rs from Σd² and n (2 dp) → rs from 5 pairs (2 dp) → rs from 7 pairs (3 dp); no ties |
| `statistics.probability` G | "Probability" | tree diagram, probability, expected frequency, independent events, relative frequency | single event (fraction `simplest`) → expected frequency → P(not) / mutually exclusive → independent AND → without replacement |
| `statistics.index_numbers` G | "Index numbers & time series" | chain base index, index numbers, moving average, time series, weighted index | index → price from index (£, 2 dp) → % change → chain base → moving average |

**Biology** (`biology.py` + pack). Rows: `Cells & transport` (cells): cells, magnification | `Organisation & disease` (organisation): organisation / `Bioenergetics & homeostasis` (bioenergetics): bioenergetics, data_maths | `Genetics & ecology` (genetics_ecology): genetics_ecology, punnett. Optional extra: `biology.quadrats` G.

| Skill | Title | Aliases | Ladder or mix |
|---|---|---|---|
| `biology.cells` B (M2) | "Cells, microscopy & transport" | cell structure, cells, organelles, microscopy, diffusion, osmosis, active transport, mitosis, stem cells | — |
| `biology.magnification` G | "Magnification" | magnification, image size, actual size, microscope calculation | M = I/A → A = I/M → mm↔µm → mixed units → standard form (`std_answer`, sf 3) |
| `biology.organisation` B (M2) | "Organisation & disease" | digestive system, enzymes, heart, blood vessels, transpiration, pathogens, vaccination, antibiotics, immune system | — |
| `biology.bioenergetics` B (M2) | "Bioenergetics & homeostasis" | photosynthesis, respiration, anaerobic, homeostasis, nervous system, reflex arc, hormones, insulin | — |
| `biology.data_maths` G | "Biology maths" | percentage change in mass, rate of photosynthesis, biology maths, inverse square law | % change (1 dp) → negative % change from masses → mean without the anomaly → rate (3 sf) → relative light intensity 1/d² (3 sf) |
| `biology.genetics_ecology` B (M2) | "Genetics, evolution & ecology" | natural selection, dna, genetics, alleles, evolution, variation, classification, ecosystems, food chains, biodiversity, carbon cycle | — |
| `biology.punnett` G | "Genetic crosses" | punnett square, genetic cross, probability of offspring, genotype, phenotype | Aa × aa (fraction) → Aa × Aa → percentage → ratio (`simplest`) → expected number out of N, or both of two offspring recessive (fraction) |

**Chemistry** (`chemistry.py` + pack). Rows: `Atoms, bonding & structure` (atoms_bonding): atoms_bonding, mr | `Quantitative chemistry` (quantitative): moles, concentration, yield_economy / `Reactions, rates & energy` (reactions): reactions, rates | `Organic, analysis & Earth` (organic_earth): organic_earth, rf_values. Required extra: `chemistry.bond_energy` G.

Every Ar value used in a question is given in that question.

| Skill | Title | Aliases | Ladder or mix |
|---|---|---|---|
| `chemistry.atoms_bonding` B (M2) | "Atoms, bonding & structure" | atomic structure, isotopes, electron configuration, periodic table, group 1, group 7, ionic bonding, covalent bonding, metallic bonding | — |
| `chemistry.mr` G | "Relative formula mass" | relative formula mass, mr, relative atomic mass, percentage by mass | simple Mr → brackets → hydrates → % by mass (1 dp) → Ar from isotope abundances (1 dp) |
| `chemistry.moles` G | "Moles" | moles calculation, moles, mole, reacting masses, avogadro | n = m/Mr → m = n × Mr → Mr then n (3 sf) → reacting masses (3 sf) → particles (standard form, 3 sf) |
| `chemistry.concentration` G | "Concentration & gas volumes" | concentration, g/dm3, mol/dm3, titration, molar gas volume | g/dm³ → cm³→dm³ → mol/dm³ → titration 1:1 (3 sf) → titration 1:2, or gas volume at RTP (24 dm³ stated) |
| `chemistry.yield_economy` G | "Percentage yield & atom economy" | percentage yield, atom economy, theoretical yield | % yield (1 dp) → atom economy → theoretical mass (3 sf) → % yield with a calculation → atom economy from an equation |
| `chemistry.reactions` B (M2) | "Chemical changes & energy" | reactivity series, acids and alkalis, salts, electrolysis, oxidation, exothermic, endothermic, collision theory, catalysts, equilibrium | — |
| `chemistry.rates` G | "Rates of reaction" | mean rate of reaction, rate of reaction, rate calculation | g/s → cm³/s with min→s → rate between two readings → mol/s (3 sf) → time from a rate |
| `chemistry.organic_earth` B (M2) | "Organic chemistry, analysis & the Earth" | crude oil, alkanes, alkenes, cracking, alcohols, polymers, chromatography, flame tests, gas tests, atmosphere, greenhouse gases, potable water | — |
| `chemistry.rf_values` G | "Chromatography Rf values" | rf value, chromatography calculation | Rf (2 dp) → mixed units → spot distance → solvent front → identify the substance (choice) |
| `chemistry.bond_energy` G | "Bond energies" | bond energies, bond energy, energy change calculation | bonds broken → bonds made → overall ΔH with its sign → several molecules → unknown bond energy |

**Computer Science** (`computer_science.py` + pack). Rows: `Data representation` (data_rep): binary, data_units | `Computer systems` (systems): systems / `Networks & security` (networks): networks | `Algorithms & programming` (algorithms): algorithms, logic.

Code in questions uses Python syntax, never `**`. Every data-size question states "Use 1 kilobyte = 1000 bytes".

| Skill | Title | Aliases | Ladder or mix |
|---|---|---|---|
| `computer_science.binary` G | "Binary & hexadecimal" | binary conversion, binary, denary, hexadecimal, hex, binary addition, binary shift | binary→denary (number) → denary→8-bit binary (short; accept the 8-bit form and the nibble-spaced form) → hex↔denary (short / number) → binary↔hex → 8-bit addition with overflow, or shifts (short) |
| `computer_science.data_units` G | "Data units & file sizes" | file size, image file size, sound file size, bits and bytes, colour depth, sample rate | bits→bytes → KB↔MB → image size → sound size (3 sf) → colours from n bits, or bits needed |
| `computer_science.logic` G | "Logic gates & truth tables" | logic gates, truth table, boolean logic, and gate, or gate, not gate, xor | one gate (number 0/1) → two gates → name the gate (choice, ref) → 3-input expression → how many truth-table rows give 1 |
| `computer_science.systems` B (M2) | "Computer systems" | fetch decode execute, cpu, von neumann, cache, ram, rom, virtual memory, secondary storage, operating system, compiler, interpreter | — |
| `computer_science.networks` B (M2) | "Networks & cyber security" | network topologies, networks, lan, wan, protocols, ip address, mac address, malware, phishing, sql injection, encryption, firewall | — |
| `computer_science.algorithms` B (M2) | "Algorithms & programming" | binary search, linear search, bubble sort, merge sort, insertion sort, pseudocode, trace table, data types, iteration, validation, sql | — |

**Astronomy** (`astronomy.py` + pack). Rows: `Earth, Moon & Sun` (earth_moon_sun): earth_moon_sun | `The Solar System` (solar_system): solar_system, orbits / `Stars & galaxies` (stars_galaxies): stars_galaxies, distances | `Observing the sky` (observing): observing.

| Skill | Title | Aliases | Ladder or mix |
|---|---|---|---|
| `astronomy.earth_moon_sun` B (M2) | "Earth, Moon & Sun" | phases of the moon, eclipses, tides, seasons, sidereal day, sunspots, aurora | — |
| `astronomy.solar_system` B (M2) | "The Solar System" | planets, dwarf planets, asteroids, comets, meteors, space probes, solar system formation | — |
| `astronomy.orbits` G | "Orbits & Kepler's third law" | kepler's third law, orbital period, astronomical unit, orbital speed | AU↔km (standard form, 3 sf; the conversion is given) → T from a (T² = a³) → a from T → v = 2πr/T → light travel time in minutes |
| `astronomy.stars_galaxies` B (M2) | "Stars, galaxies & cosmology" | stellar evolution, hr diagram, red giant, supernova, black hole, galaxies, redshift, big bang, exoplanets, parallax | — |
| `astronomy.distances` G | "Distances & Hubble's law" | hubble's law, light year, parsec, parallax calculation, distance modulus | ly↔pc → d = 1/p → v = H₀d (H₀ stated) → d from v → distance modulus (1 dp) |
| `astronomy.observing` B (M2) | "Observing the sky" | telescopes, reflecting telescope, refracting telescope, constellations, celestial sphere, declination, light pollution, radio telescope | — |

### 5.2 content-2 (English and performance; all bank files)

| Subject (mix) | Rows | Skills: "Title" (first aliases) |
|---|---|---|
| English Language (M1) | `Language techniques` (techniques) \| `Reading & structure` (reading) / `Grammar & punctuation` (spag) \| `Writing skills` (writing) | `english_language.techniques` "Language techniques" (language techniques, metaphor, simile, personification, alliteration, pathetic fallacy, semantic field, hyperbole); `.reading` "Reading & structure" (structural features, foreshadowing, flashback, cyclical structure, narrative perspective, inference); `.spag` "Grammar & punctuation" (spag, word classes, sentence types, clauses, apostrophes, homophones, punctuation); `.writing` "Writing skills" (persuasive devices, writing to argue, audience and purpose, form, discourse markers, paragraphing). Reading extracts are original or public domain, ≤ 80 words. |
| English Literature (M1) | `Macbeth` (macbeth) \| `A Christmas Carol` (christmas_carol) / `An Inspector Calls` (inspector_calls) \| `Conflict poetry` (conflict_poetry) | `english_literature.macbeth` "Macbeth" (macbeth, lady macbeth, banquo, the witches); `.christmas_carol` "A Christmas Carol" (a christmas carol, scrooge, marley, tiny tim, dickens); `.inspector_calls` "An Inspector Calls" (an inspector calls, inspector goole, birling, priestley, sheila, eric), **no quotations**; `.conflict_poetry` "Conflict poetry" (conflict poetry, power and conflict, ozymandias, london, charge of the light brigade, exposure, my last duchess, remains, poppies, war photographer, kamikaze), quotes only from public-domain poems. **Required extras:** `.romeo_juliet` "Romeo and Juliet" (romeo and juliet, romeo, juliet, mercutio, tybalt); `.jekyll_hyde` "Jekyll and Hyde" (jekyll and hyde, dr jekyll, mr hyde, utterson, stevenson). **Optional:** blood_brothers (no quotations), frankenstein, great_expectations, pride_prejudice, jane_eyre, love_poetry, poetry_terms. |
| Drama (M1) | `Roles & stages` (roles_stages) \| `Practitioners & styles` (practitioners) / `Performance skills` (performance) \| `Design & technical` (design) | `drama.roles_stages` "Theatre roles & stages" (stage types, proscenium, thrust stage, traverse, in the round, stage directions, upstage, director, stage manager); `.practitioners` "Practitioners & styles" (stanislavski, brecht, artaud, frantic assembly, epic theatre, naturalism, physical theatre, verbatim theatre, commedia dell'arte); `.performance` "Performance skills" (vocal skills, physical skills, pitch, pace, projection, gesture, proxemics, hot seating, thought tracking, still image); `.design` "Design & technical" (lighting design, sound design, set design, costume, gobo, gel, fresnel, cyclorama). No set-text quotations. |
| Media Studies (M1) | `Media language` (language) \| `Representation` (representation) / `Media industries` (industries) \| `Audiences` (audiences) | `media_studies.language` "Media language" (media language, semiotics, denotation, connotation, genre codes, narrative theory, todorov, propp, binary opposition, masthead); `.representation` "Representation" (stereotypes, representation, gender representation, mediation, selection, construction); `.industries` "Media industries" (media ownership, conglomerate, vertical integration, regulation, ofcom, bbfc, pegi, convergence, public service broadcasting); `.audiences` "Audiences" (target audience, demographics, psychographics, uses and gratifications, hypodermic needle, two-step flow, cultivation theory, reception theory). No board set products. |
| Film Studies (M1) | `Cinematography & editing` (cinematography) \| `Mise-en-scène & sound` (mise_en_scene) / `Genre & narrative` (genre_narrative) \| `Film history & industry` (history_industry) | `film_studies.cinematography` "Cinematography & editing" (camera shots, camera angles, camera movement, continuity editing, montage, match on action, shot reverse shot, cross-cutting, jump cut); `.mise_en_scene` "Mise-en-scène & sound" (mise-en-scene, mise en scene, low key lighting, high key lighting, costume, diegetic sound, non-diegetic sound, foley, sound bridge); `.genre_narrative` "Genre & narrative" (film genre, iconography, three-act structure, protagonist, auteur, spectatorship); `.history_industry` "Film history & industry" (film history, silent cinema, studio system, classical hollywood, new hollywood, independent film, distribution, exhibition, film certificates, cgi) |

### 5.3 content-3 (Humanities)

| Subject (mix) | Rows | Skills |
|---|---|---|
| History (M1, bank) | `Germany 1890–1945` (germany) \| `Elizabethan England` (elizabethan) / `Medicine through time` (medicine) \| `Cold War` (cold_war) | `history.germany` "Germany 1890–1945" (nazi germany, weimar, germany, kaiser wilhelm, treaty of versailles, hyperinflation, munich putsch, reichstag fire, hitler youth); `.elizabethan` "Elizabethan England" (elizabethan england, elizabeth i, mary queen of scots, spanish armada, puritans, poor law, religious settlement); `.medicine` "Medicine through time" (medicine through time, health and the people, four humours, galen, vesalius, jenner, pasteur, koch, fleming, penicillin, nhs, public health); `.cold_war` "Cold War" (cold war, superpower relations, berlin wall, cuban missile crisis, truman doctrine, marshall plan, berlin blockade, nato, warsaw pact, arms race). **Optional extras:** america, conflict_1918_1939, norman_england, ww1, crime_punishment. No short answer may be exactly "Cold War". |
| Geography (`geography.py` + pack; M1 banks) | `Natural hazards` (hazards) \| `Rivers & coasts` (landscapes) / `Cities & development` (urban) \| `Geographical skills` (skills) | `geography.hazards` B "Natural hazards" (natural hazards, tectonic hazards, earthquakes, volcanoes, plate boundaries, tropical storms, extreme weather, climate change); `.landscapes` B "Rivers & coasts" (coastal landforms, rivers, coasts, erosion, deposition, longshore drift, meanders, waterfalls, spits, flood management, hydrographs); `.urban` B "Cities & development" (urbanisation, urban issues, megacities, development gap, hdi, demographic transition model, globalisation, sustainable cities, resource management); `.skills_stats` G "Geographical skills" (geographical skills, map scale, population density, statistics, percentage change, interquartile range) — range/mean → median/mode → % change (1 dp) → IQR → population density or map-scale distance. **Optional extras:** living_world B, resources B. |
| Religious Studies (M1, bank) | `Christian beliefs & practices` (christianity) \| `Muslim beliefs & practices` (islam) / `Religion & life` (religion_life) \| `Peace & conflict` (peace_conflict) | `religious_studies.christianity` "Christianity: beliefs & practices" (christianity, christian beliefs, trinity, incarnation, resurrection, salvation, sacraments, baptism, eucharist, pilgrimage); `.islam` "Islam: beliefs & practices" (islam, muslim beliefs, tawhid, five pillars, shahadah, salah, zakah, sawm, hajj, ramadan, sunni, shi'a); `.religion_life` "Religion & life" (religion and life, origins of the universe, evolution, stewardship, animal rights, abortion, euthanasia, sanctity of life, afterlife); `.peace_conflict` "Peace & conflict" (peace and conflict, just war theory, holy war, pacifism, terrorism, nuclear weapons, forgiveness, reconciliation). **Optional extras:** judaism, buddhism, hinduism, sikhism, relationships_families, crime_punishment. |
| Citizenship (M1, bank) | `Democracy & government` (democracy) \| `Rights & the law` (rights_law) / `Life in modern Britain` (modern_britain) \| `Active citizenship` (active) | `citizenship.democracy` "Democracy & government" (parliament, democracy, elections, first past the post, house of commons, house of lords, cabinet, devolution, constitution); `.rights_law` "Rights & the law" (human rights, rights, courts, magistrates, jury, criminal law, civil law, youth justice); `.modern_britain` "Life in modern Britain" (life in modern britain, identity, diversity, free press, migration, united nations, commonwealth); `.active` "Active citizenship" (active citizenship, campaigning, pressure groups, petitions, volunteering, charities, trade unions) |
| Classical Civ (M1, bank) | `Myth & religion` (myth_religion) \| `Women in the ancient world` (women) / `The Homeric world` (homeric) \| `Roman city life` (roman_city) | `classical_civilisation.myth_religion` "Myth & religion" (myth and religion, olympian gods, zeus, heracles, temples, sacrifice, underworld, romulus and remus, aeneas, theseus); `.women` "Women in the ancient world" (women in the ancient world, spartan women, athenian women, vestal virgins, livia, penelope); `.homeric` "The Homeric world" (homeric world, odyssey, iliad, odysseus, mycenae, troy, achilles, hector, xenia); `.roman_city` "Roman city life" (roman city life, pompeii, domus, insula, patrons and clients, gladiators, chariot racing, roman baths, forum). **Optional extra:** war. |

### 5.4 content-4 (Social sciences and business)

| Subject | Rows | Skills |
|---|---|---|
| Psychology (`psychology.py` + pack; M1) | `Memory & perception` (memory_perception) \| `Development & the brain` (development_brain) / `Social influence` (social_influence) \| `Research methods` (research_methods) | `psychology.memory_perception` B "Memory & perception" (multi-store model, memory, perception, short-term memory, long-term memory, reconstructive memory, serial position effect, visual illusions, perceptual set); `.development_brain` B "Development & the brain" (brain development, piaget, mindset, learning styles, neuropsychology, neurons, synapse, lobes of the brain); `.social_influence` B "Social influence" (conformity, social influence, obedience, bystander effect, crowd behaviour, deindividuation, prosocial behaviour); `.research_methods` B "Research methods" (independent variable, research methods, hypothesis, dependent variable, experimental design, sampling, ethics, reliability, validity); `.stats` G "Psychology maths" (psychology maths, mean median mode, percentages, ratio, standard form, estimating) — mean → median/mode/range → % of participants (1 dp) → ratio `simplest` → standard form or estimate. **Optional extras:** language_thought, sleep_dreaming, criminal, psychological_problems (safeguarding caution). |
| Sociology (bank, M1) | `Families` (families) \| `Education` (education) / `Crime & deviance` (crime) \| `Research methods` (methods) | `sociology.families` "Families" (family types, families, nuclear family, reconstituted family, conjugal roles, divorce, functionalist view of the family, feminist view); `.education` "Education" (hidden curriculum, education, labelling, self-fulfilling prophecy, streaming, cultural capital, material deprivation, marketisation); `.crime` "Crime & deviance" (crime and deviance, social control, strain theory, subcultures, labelling theory, moral panic, official statistics, victim surveys); `.methods` "Research methods" (participant observation, research methods, primary data, secondary data, questionnaires, interviews, sampling, positivism, interpretivism). **Optional extras:** stratification, theories. |
| Economics (`economics.py` + pack; M1 banks) | `Markets & prices` (markets) \| `Firms & production` (firms) / `Money, banks & work` (money_work) \| `The national economy` (national) | `economics.markets` B "Markets & prices" (supply and demand, markets, equilibrium price, market failure, externalities, opportunity cost, scarcity, competition); `.elasticity` G "Price elasticity" (price elasticity of demand, ped, pes, elasticity) — % change (1 dp) → PED from %s (2 dp) → PED from P and Q → PES → new quantity from PED; `.firms` B "Firms & production" (economies of scale, firms, productivity, specialisation, division of labour, objectives of firms); `.firms_maths` G "Costs, revenue & profit" (total revenue, costs, profit, average cost, fixed cost, variable cost) — TR → TC → profit → AC (£, 2 dp) → profit at an output from a table; `.money_work` B "Money, banks & work" (role of money, banks, interest rates, saving, borrowing, labour market, wages, trade unions); `.interest` G "Interest & savings" (compound interest, simple interest, real interest rate) — simple → compound (2 dp) → real rate → % change of savings → years to reach a target; `.national` B "The national economy" (economic growth, gdp, inflation, unemployment, fiscal policy, monetary policy, international trade, exchange rates, globalisation); `.macro_maths` G "Macro calculations" (inflation rate, gdp growth, exchange rate conversion, balance of trade) — inflation from CPI → GDP growth % → real growth → currency conversion (2 dp) → balance of trade (with sign) |
| Business (`business.py` + pack; M1 banks) | `Enterprise & ideas` (enterprise) \| `Marketing` (marketing) / `Operations & people` (operations_people) \| `Finance` (finance) | `business.enterprise` B "Enterprise & ideas" (business ownership, enterprise, entrepreneur, sole trader, partnership, limited liability, stakeholders, business location, franchising); `.marketing` B "Marketing" (marketing mix, market research, segmentation, product life cycle, boston matrix, pricing strategies, promotion, branding); `.operations_people` B "Operations & people" (production methods, operations, quality control, supply chain, lean production, customer service, recruitment, motivation, organisational structure); `.finance` B "Finance" (sources of finance, finance, cash flow, break-even, income statement, profit margins, average rate of return); `.finance_maths` G "Business calculations" (break-even point, break even calculation, gross profit margin, net profit margin, arr, cash flow forecast, margin of safety) — revenue/TC → gross/net profit → break-even units (rounded up) → margins (1 dp) → ARR or closing balance or margin of safety |

### 5.5 content-5 (Languages; all bank files)

- French, Spanish, German, Italian, Russian, Arabic and Mandarin share these rows: `Grammar & tenses` (grammar) | `People & lifestyle` (people) / `Free time & culture` (culture) | `Travel & the world` (world).
- The skills are `<id>.grammar`, `<id>.people`, `<id>.culture` and `<id>.world`, titled like the labels.

| Skill | First alias | Other aliases |
|---|---|---|
| `<id>.grammar` | `<language> grammar` (e.g. "french grammar") | tenses, present tense, past tense, future tense, conditional, verbs, adjective agreement, pronouns, negatives, plus target-language terms (passé composé, pretérito, Perfekt, passato prossimo, падежи) |
| `<id>.people` | `<language> family` | family, friends, describing people, personality, school, healthy living, daily routine, jobs, future plans |
| `<id>.culture` | `<language> free time` | hobbies, sport, music, cinema, tv, technology, social media, festivals, food and drink |
| `<id>.world` | `<language> holidays` | holidays, travel, town, local area, home, environment, global issues, weather, directions, transport, shopping |

- **Mixes:** M3 for French, Spanish, German, Italian and Russian (at most 30% of Russian items require typing Cyrillic). M4 for Arabic and Mandarin.
- **Answer forms:** translations into English use form `any`; answers in the target language use `strict`; Mandarin pinyin uses `pinyin`.
- **Latin** (`latin`, M3; answers in English or unaccented Latin, no macrons). Rows: `Nouns & cases` (nouns) | `Verbs & tenses` (verbs) / `Vocabulary & translation` (vocab) | `Roman life & myths` (roman_life).
  - `latin.nouns` "Nouns & cases" (latin cases, nominative, accusative, genitive, dative, ablative, declensions, adjectives, prepositions);
  - `latin.verbs` "Verbs & tenses" (latin verbs, imperfect tense, perfect tense, pluperfect, infinitive, imperative, participles, passive, irregular verbs);
  - `latin.vocab` "Vocabulary & translation" (latin vocabulary, vocab, translation, english derivatives);
  - `latin.roman_life` "Roman life & myths" (roman life, roman myths, roman family, roman religion, roman army, roman britain).

### 5.6 content-6 (Creative and practical; all bank files, M2, no rubric)

| Subject | Rows | Skills |
|---|---|---|
| Music | `Elements of music` (elements) \| `Notation & theory` (theory) / `Instruments & ensembles` (instruments) \| `Styles & history` (styles) | `music.elements` "Elements of music" (elements of music, dynamics, tempo, rhythm, melody, harmony, texture, timbre, structure, italian terms, ostinato, syncopation, cadence); `.theory` "Notation & theory" (note values, notation, time signature, key signature, scales, intervals, chords, clefs, dotted notes); `.instruments` "Instruments & ensembles" (orchestral instruments, instruments, orchestra, woodwind, brass, strings, percussion, voice types, pizzicato, string quartet, music technology); `.styles` "Styles & history" (baroque music, music history, classical period, romantic period, minimalism, film music, popular music, jazz, blues, reggae, bhangra, samba). Beat-counting items may use `answer` with kind number. |
| Design & Tech | `Materials & properties` (materials) \| `Energy, systems & mechanisms` (energy_systems) / `Making & manufacturing` (making) \| `Design & sustainability` (design) | `design_technology.materials` "Materials & properties" (properties of materials, hardwoods, softwoods, manufactured boards, ferrous metals, alloys, thermoplastics, textiles, smart materials, composites); `.energy_systems` "Energy, systems & mechanisms" (gear ratio, energy generation, renewable energy, batteries, input process output, sensors, levers, linkages, cams, pulleys, types of motion); `.making` "Making & manufacturing" (scales of production, batch production, mass production, cad, cam, cnc, 3d printing, jigs, moulds, tolerances, finishes); `.design` "Design & sustainability" (iterative design, design strategies, user-centred design, specification, the 6 rs, life cycle assessment, planned obsolescence, ergonomics, anthropometrics, famous designers) |
| Food & Nutrition | `Nutrients & health` (nutrients) \| `Food science` (science) / `Food safety` (safety) \| `Food choice & provenance` (choice) | `food_nutrition.nutrients` "Nutrients & health" (macronutrients, nutrients, micronutrients, protein, carbohydrates, fats, vitamins, minerals, fibre, eatwell guide, life stages); `.science` "Food science" (gelatinisation, food science, cooking methods, conduction, convection, denaturation, coagulation, caramelisation, emulsification, raising agents, gluten); `.safety` "Food safety" (food poisoning, food safety, bacteria, danger zone, high risk foods, cross-contamination, use by, best before, food storage); `.choice` "Food choice & provenance" (food provenance, food labelling, allergies, intolerances, food miles, organic food, seasonal food, food waste, primary processing, international cuisines) |
| PE | `Anatomy & physiology` (anatomy) \| `Movement & training` (training) / `Sport psychology` (psychology) \| `Health & sport in society` (society) | `pe.anatomy` "Anatomy & physiology" (skeletal system, anatomy, joints, muscles, antagonistic pairs, cardiovascular system, respiratory system, aerobic, anaerobic, epoc, cardiac output); `.training` "Movement & training" (components of fitness, fitness tests, principles of training, fitt, interval training, circuit training, fartlek, plyometrics, training zones, warm up, levers, planes and axes); `.psychology` "Sport psychology" (skill classification, sport psychology, open skills, closed skills, smart targets, guidance, feedback, arousal, inverted u, motivation); `.society` "Health & sport in society" (commercialisation of sport, participation, sponsorship, the media, sportsmanship, gamesmanship, performance-enhancing drugs, hydration, energy balance, well-being) |
| Art & Design | `Formal elements` (formal) \| `Colour theory` (colour) / `Media & techniques` (media) \| `Art history & movements` (history) | `art_design.formal` "Formal elements" (formal elements, line, tone, shape, form, texture, pattern, composition, perspective, proportion, negative space); `.colour` "Colour theory" (colour wheel, colour theory, primary colours, secondary colours, complementary colours, warm colours, tint, shade, hue); `.media` "Media & techniques" (printmaking, drawing techniques, watercolour, acrylic, lino print, collage, sculpture, ceramics, hatching, impasto, sgraffito); `.history` "Art history & movements" (art movements, art history, renaissance, impressionism, cubism, surrealism, expressionism, pop art, abstract expressionism, famous artists) |

---

## 6. Content rules (copy verbatim to every content agent)

```
R1  Original questions only. Never copy or closely paraphrase exam-board papers, specimen papers, mark schemes,
    textbooks or revision sites. Write each question yourself.
R2  No quotations from copyrighted works (e.g. An Inspector Calls, Blood Brothers, Of Mice and Men, modern
    anthology poems such as Remains, Poppies, War Photographer, Kamikaze). Plot, character, theme, context and
    structure facts are fine. Short quotes (<= 15 words) from public-domain texts are fine: Shakespeare, Dickens,
    Stevenson, Shelley (Mary and Percy), Austen, Brontë, Owen, Blake, Tennyson, Wordsworth, Browning.
R3  Exactly one unambiguous correct answer. No opinion questions, no "best" without a clear criterion, no "which
    TWO", no "all/none of the above", no options that refer to other letters. 3–5 options; distractors are
    plausible but clearly wrong. Never use a lone letter as an option ("Group A", not "A").
R4  Facts must be true across exam boards (AQA, Edexcel, OCR, WJEC/Eduqas, Cambridge IGCSE), or the question must
    be phrased so it is ("Many Christians believe…", "In the multi-store model…"). No facts that expire: no current
    office holders, current interest/tax/wage rates, current records or "latest" anything.
R5  Age-appropriate and respectful. RS: multi-faith and neutral; attribute beliefs to believers ("Muslims
    believe…"), never state religious claims as facts or rank religions. History: sensitive topics (the Holocaust,
    slavery, war) are factual and respectful, never trivia-style, with no graphic detail. Food and PE: never promote
    dieting, weight loss, calorie restriction or body ideals. Reproduction and health: curriculum-level facts only.
    No sexual violence details.
R6  Safety words: no accepted answer or option may be, or need, a distress or self-harm word (e.g. suicide,
    self-harm, overdose, abused, bullied, nudes). Use "assisted dying", not "assisted suicide". The audit and the
    tests reject these.
R7  Short answers: say exactly what to type ("Give the term.", "Name the …", "Give the year.", "Answer in English.",
    "Translate into French. Include the article."). List every reasonable variant in accept (surname only and full
    name, "NHS" and "National Health Service", "World War Two"/"Second World War"/"WW2"). List real terms within one
    or two letters in reject (alkane/alkene, mitosis/meiosis, affect/effect). Never put accent-less spellings in
    accept: the checker accepts them automatically with a note. Chemical formulae and symbols use form "case".
    Years only for AD dates; BC dates are multiple choice only.
R8  Languages: correct target-language spelling, accents and characters (é, ñ, ß, ü, Cyrillic). Answers in the
    target language use form "strict". Arabic: choice or English answers only, one Arabic word or phrase per option,
    no Latin text inside an Arabic option. Mandarin: choice, English or pinyin answers (form "pinyin"); hanzi in
    stems and options, with pinyin in brackets at levels 1–3. Russian: at most 30% of items require typing Cyrillic.
    Latin: no macrons.
R9  Plain text only: no Markdown, no LaTeX, no "**", "`", "$", "\", "#" headings. Use × ÷ ² ³ √ π °. Code (Computer
    Science) is Python syntax without "**". Text <= 600 chars including options; solution <= 300 chars, no trailing
    period; hints give a first step and never contain the answer or the correct option text.
R10 Levels: L1 recall, L2 discrimination/short recall, L3 apply to a simple new example, L4 two steps or a short
    data/extract interpretation, L5 exam-style reasoning. >= 30 questions per bank skill, >= 4 per level (aim for 6),
    choice + short >= 85%. Rubric only in the subjects allowed by section 5, levels 4–5 only, <= 15% of a skill,
    with a model answer <= 600 chars and a mark scheme (one line per mark point).
R11 Every question has a unique "id" within its skill; no two questions in a skill share the same stem. A
    "topic_note" (<= 40 chars) names the text, period or case study when the question would be unclear in mixed
    Past paper practice ("Macbeth", "Weimar Republic").
R12 No short answer may equal a topic label of the subject, "Past paper practice", "My own topic", or a button text.
    Answers and options must not be words the bot treats as commands (help, hint, skip, pass, next, explain).
R13 Calculations: give every constant and data value the question needs (Ar values, g, H0, "1 kilobyte = 1000 bytes"),
    state rounding and units, and use display units the checker knows.
R14 Before handing in: "python3 -m tutor audit --file <your file>" (or "--subject <id>") must show no ERROR lines;
    spot-check with "python3 -m tutor sample SKILL_ID LEVEL 5".
```

---

## 7. Tests (test-dev)

**Rules (in addition to v1 §6)**
- Write the tests from this document, not from the code. Hard-code the golden texts.
- The default run must take under 60 s. Time budget: `test_skills` ≤ 30 s, `test_content_banks` ≤ 12 s, everything else ≤ 15 s.
- Generator skills: 30 seeds per level by default, 300 with `TUTOR_FULL_TESTS=1`. Bank items: seeds 0–3 per item by default, 0–19 in the full run.
- Report timings. If the default run takes more than 55 s, lower generator seeds to 20 (never below) and report it.
- Do not fix the implementation or the content. Report failures by owning agent.

**Files**

| File | Covers |
|---|---|
| `tests/helpers.py` | New golden texts (§3.1, §2.3 constants); `SUBJECT_TITLES_10_11` (35, in §4 order); `SUBJECT_KB_10_11`; `choice_row(n)`; `perturb`: choice → letter of the first wrong option, short → `"qq" + display + "qq"`, others as v1; `keyboard_problem` knows all 35 titles plus "Demo" |
| `tests/test_checker.py` | Unchanged: all v1 rows must still pass |
| `tests/test_answer_kinds.py` (new) | Both §2.3 tables exactly; mistake feedback; exact note strings; `build_choice` (deterministic, displayed order, display, mistakes, ValueError cases); `build_short`; `shuffle_order`; `letters_text`; JSON round-trip with `ref`; `fingerprint` |
| `tests/test_bank.py` | v1 cases plus v2 fixtures: all kinds, `topic_note`, `"10,11"` keys with `{year}`, `load_pack`, refs `<skill>#<id>`, `items`, selection `seed % n`, nearest level, trailing-period stripping, cache returns the same objects; every invalid fixture raises `BankError` with its JSON path; auto-reject fixture: an option "alkene" elsewhere in the file makes short "alkane" reject `alkene` while `alkanes` is correct with a note |
| `tests/test_content_banks.py` (new) | **Every shipped skill that has items:** per item and seed: render is deterministic and survives JSON round-trip; display correct with no note; perturb not correct. Choice: every wrong letter wrong (with its feedback), the correct letter in lower case correct, the correct option text correct, the text lists the options in displayed order; the correct letter takes ≥ 2 values over seeds 0–19; per skill, every letter position's share is within [0.5/n, 1.5/n]. Short: each accept correct, upper-case display correct (not `case`), `"the " + display` correct (`any`), folded display correct with NOTE_ACCENTS when it differs, an adjacent-letter swap of eligible accepts correct with NOTE_SPELLING (skipped when within distance of a reject), each reject wrong (with feedback), lower-cased `case` display → FORM_CASE. Lint rules L1–L11 below. |
| `tests/test_skills.py` | Generator skills only (`not skill.items`); REQUIRED = v1 ids plus every G id in §5 except optional extras; seeds 30/300 |
| `tests/test_registry.py` | `subjects_for_year(10)` and `(11)` titles == the §4 list in order; Years 7–9 = `["Maths"]`; `years() == [7..11]`; `topic_rows` for every subject == §5; past-paper union; letters A–E reserved; dash-insensitive labels; accent-folded aliases (`passe compose` → `french.grammar`); first-alias match; strict `load_registry` raises on a broken extra bank; non-strict skips it and fills `load_errors`; `load_registry()` < 10 s |
| `tests/test_flow.py` | SUBJECT_ASK with the exact 35-subject keyboard; Year 8 shows Maths only; English Literature → TOPIC_ASK with its keyboard; keyboard invariant on every reply |
| `tests/test_lesson.py` | Custom registry with choice, short, rubric and number skills: choice problem → PROBLEM_CHOICE + `choice_kb(n, rows)`; tapping a letter marks; distractor feedback in WRONG; WHY_FACT fallback; CHOICE_UNPARSED with letters text; hint and cheat replies keep the letter row; a following number problem has no letter row; short typo → CORRECT_NOTE; FORM_CASE in WRONG; SHORT_UNPARSED; past paper gives `(1 mark)`; rubric → PROBLEM_RUBRIC then UNMARKABLE with no attempt even with a FakeLLM when `llm_marking=False` |
| `tests/test_repeat.py` (new) | A 6-item level gives 6 different refs over 6 skips, then the least recently seen one; never the same problem twice in a row (2-item level alternates); never two rubric problems in a row; `seen` pruned to 30; persists across restart; `/delete_my_data` and `/reset` clear it |
| `tests/test_persistence.py` | Migration: a file DB built from the v1 §3.3 SQL with `schema_version` '1' and a v1 pending row (no `ref`) → after opening, version '2', `seen` table exists, pending loads with `ref == ""` |
| `tests/test_llm.py` | `leaks_answer` for choice and short; rubric marking only when `llm_marking=True` |
| `tests/test_config.py` | `TUTOR_LLM_MARKING` values |
| `tests/test_safety.py` | New exact skip phrases; `"not sure what photosynthesis is"` is not a skip |
| `tests/test_cli.py` | `audit --file` on the valid fixture → exit 0; on an invalid fixture → exit 1 with ERROR; `sample <bank skill> 1 2` → exit 0 and lines `A)`; `--check` without a token unchanged |
| `tests/fixtures/` | `bank_v2_sample.json`, `pack_sample.json`, `repeat_bank.json`, `bank_v2_invalid/<case>.json` with one case per file: two_options, correct_out_of_range, duplicate_options, all_of_the_above, lone_letter_option, feedback_on_correct, empty_accept, accept_reject_overlap, unknown_key, duplicate_id, duplicate_stem, text_too_long, hint_leaks, bad_form, rubric_no_model, choice_via_answer_key |

**Lint rules (tests and audit; ERROR unless marked WARN)**

| Rule | Check |
|---|---|
| L1 | Every question in shipped files has an `id` |
| L2 | Each required bank skill has ≥ 30 questions and ≥ 4 per level 1–5; optional extras have the same minimum if they are shipped |
| L3 | choice + short ≥ 85% of a skill |
| L4 | Rubric only in §5-allowed subjects, only at levels 4–5, at most `floor(0.15 × total)` items |
| L5 | No accept or option text is a distress phrase, an intent, or a cheat request (checked with `is_distress`, `intent`, `is_cheat_request`) |
| L6 | No short accept equals a topic label of the subject (any year, casefolded, dash-folded), a reserved label or a button text. Choice options equal to a label → WARN (audit only) |
| L7 | No Markdown or LaTeX in text, solution, hint, options or feedback: `**`, `` ` ``, `$`, `\`, lines starting with `#` |
| L8 | Subject titles ≤ 18 characters; new topic labels ≤ 30 |
| L9 | ≥ 3 lowercase aliases per skill; `match_skills(subject, first_alias)[0] == skill.id` |
| L10 | The choice letter variation rules above |
| L11 | Arabic and Mandarin accepts contain no Arabic script and no hanzi; Russian Cyrillic accepts ≤ 30% of a skill |

---

## 8. Risks

1. **Accuracy at volume.** About 3,750 hand-written questions. The tests prove the questions are consistent with themselves, not that they are true. Mitigation: a critic pass per subject (a 10% sample plus every L5 item), `sample` spot-checks and owner spot-checks before release.
2. **Exam boards differ.** Each subject offers 4 board-neutral topics (the most common options and texts). Many students will need «My own topic» extras that are only optional in v2.
3. **Typo tolerance can accept a different term** (alkane/alkene). Mitigations: reject lists, automatic rejects, the same-first-letter rule, letters-only answers of 6+ characters, and none in `strict`/`case`/`pinyin`. Pairs nobody listed can still slip through; watch `/student` records.
4. **Multiple-choice guessing (25–33%)** makes levels noisy. The mix with short answers limits it; a "two correct in a row" rule is out of scope.
5. **Copyright and memorised past papers.** Agents may reproduce known questions without noticing (R1, R2). Reviewers must check samples.
6. **Safeguarding.** Sensitive themes (RS ethics, the Holocaust, mental health, food and body image) are handled by rules R5 and R6 and lint L5. Some student phrasings will still trigger DISTRESS as a false positive.
7. **Display.** Arabic (right-to-left) mixed with the "A)" prefix may render oddly in Telegram. The 19-row subject keyboard is long on small phones.
8. **Time.** Test runtime and startup time (registry load about 1–3 s) are at the edge. Bank parsing is cached and seed budgets are set in §7.
9. **Workload per agent.** content-5 has about 960 questions and content-2 about 750. Splitting by file is allowed.
10. **Old DB rows.** Pending rows without `ref` load with `""`. A v2 database opened by v1 code ignores `seen`, so a rollback is safe.

## 9. Owner decisions (12 Nov 2026)

- All 35 subjects ship at once (no waves).
- Exam boards / set texts: use the defaults in §5 for now.
- Extended practice (rubric with model answer, unmarked) is kept as planned.
- Subject order: core-first as in §4.

## 9a. Original open questions (answered above)

1. **Release: all 35 subjects at once, or in waves?** The tests require the full list, so waves would need the lead to set the expected subject list for each wave.
2. **Which exam boards and set texts do your students take?** v2 picks the most common (Macbeth, A Christmas Carol, An Inspector Calls, conflict poetry; History: Germany, Elizabethan England, Medicine, Cold War). The answer decides which optional extras are written first.
3. **Extended practice (rubric items with a model answer, no marking, at most 15%):** keep it as planned, or drop it entirely?
4. **Subject order:** is core-first (Maths, English, sciences, then groups) OK, or should the order follow your list exactly?

### Critical files
- /home/claude/claudemaxalan/tutor/content/base.py
- /home/claude/claudemaxalan/tutor/content/checker.py
- /home/claude/claudemaxalan/tutor/content/bank.py
- /home/claude/claudemaxalan/tutor/content/registry.py
- /home/claude/claudemaxalan/tutor/engine.py
- /home/claude/claudemaxalan/tutor/db.py
- /home/claude/claudemaxalan/tutor/texts.py
- /home/claude/claudemaxalan/tests/helpers.py
- /home/claude/claudemaxalan/tests/test_skills.py
- /home/claude/claudemaxalan/docs/ARCHITECTURE.md
## 10. Implementation notes (lead, 12 Nov 2026 — these amend the sections above)

- **Choice shuffle salt (§2.2, §2.4):** `shuffle_order(n, seed, salt="")`. Bank items call it with `salt=ref`, so letter positions do not depend on where authors put the correct option in the file. Without a salt the §2.2 formula is unchanged.
- **Option text with a hyphen (§2.3 choice):** a line such as `e-books` or `D-Day` that equals an option as a whole names that option; it is not read as the letter E/D. `A - Mitochondria` (spaced) is still rule (b).
- **Accepts with fillers:** accepts are also compared after filler stripping, so an accept such as `it is carried` can match. Audit WARNs on such accepts and ERRORs if any accept is not judged correct.
- **ß:** survives casefolding; `strasse` for `straße` is correct with NOTE_ACCENTS. **Pinyin:** `v` = `ü`.
- **Numeric short answers:** digit tokens are digit groups not glued to letters (`qq1918qq` is not 1918).
- **Reason/check lines:** `sub`/`substitute` count as check words only with a digit or `=` on the line; `as` counts as a reason word only when text follows; a line that equals an option/accept is never discarded as a reason line. Fillers never consume a whole line.
- **`leaks_answer` (§3.4):** for choice/short only the §3.4 rules apply (no v1 substring test); the letter pattern is case-insensitive.
- **Skip phrases:** exact skip phrases ignore trailing `.,`.
- **Auto-rejects:** exclude plural variants both ways, are sorted by distance, and are built only for typo-eligible accepts.
- **`/reset`** also clears the student's `seen` rows.
- **Audit:** shipped-content rules (L1–L4, L6, L8, L9, L11, kind mixes, the §4 table) apply only to `banks/`, `packs/` and subject modules, not to test fixtures. Audit WARNs on short items whose stem starts with "Why".
- **Known contract limit:** options or accept/reject pairs that differ only by an apostrophe (its / it's) cannot coexist.
