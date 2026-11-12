"""docs/ARCHITECTURE_V2.md sections 5 and 7: every shipped skill with bank items (banks and packs), plus lint rules L1-L11.

Failures are attributed to the owning content agent (section 1) in the assertion messages.
Budget: default seeds 0-3 per item, full run (TUTOR_FULL_TESTS=1) seeds 0-19.
"""
import json
import os
import re
import unicodedata
import unittest
from collections import Counter, defaultdict

import helpers
import spec
from helpers import FORM_CASE, NOTE_ACCENTS, perturb
from tutor.content import check, load_registry, problem_from_json, problem_to_json, BANKS_DIR, PACKS_DIR
from tutor.intents import intent, is_cheat_request, is_distress

FULL = os.environ.get("TUTOR_FULL_TESTS") == "1"
SEEDS = range(20) if FULL else range(4)
VARIATION_SEEDS = range(20)
LETTERS = "ABCDE"

SUBJECT = {s["id"]: s for s in spec.SUBJECTS}
NEW_SUBJECTS = [s for s in spec.SUBJECTS if s["source"] != "frozen"]


def owner_of(skill_id):
    sid = skill_id.split(".")[0]
    return SUBJECT[sid]["owner"] if sid in SUBJECT else "unknown-owner"


_STATE = {}


def registry():
    if "reg" not in _STATE:
        _STATE["reg"] = load_registry()      # strict: a broken content file raises here
    return _STATE["reg"]


def bank_skills():
    """All registry skills that have bank items (any subject)."""
    if "skills" not in _STATE:
        reg = registry()
        out = []
        ids = []
        for yr in reg.years():
            for s in reg.subjects_for_year(yr):
                if s.id not in ids:
                    ids.append(s.id)
        for sid in ids:
            out.extend(sk for sk in reg.skills_of(sid) if sk.items)
        _STATE["skills"] = out
    return _STATE["skills"]


def report(testcase, fails, what):
    if not fails:
        return
    by_owner = Counter(f.split("]")[0] + "]" for f in fails)
    testcase.fail(f"{what}: {len(fails)} failure(s) by owner {dict(by_owner)}; first 12:\n" + "\n".join(fails[:12]))


def norm_basic(s):
    s = unicodedata.normalize("NFC", s).casefold().replace("’", "'")
    s = s.replace("'", "")
    s = re.sub(r"[-/]", " ", s)
    s = re.sub(r"[^\w\s.]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"^(the|a|an) (?=.)", "", s)


def fold_plain(s):
    out = []
    for ch in s:
        if ch in "ßæœøł":
            out.append({"ß": "ss", "æ": "ae", "œ": "oe", "ø": "o", "ł": "l"}[ch])
            continue
        dec = unicodedata.normalize("NFKD", ch)
        base = dec[0]
        if len(dec) > 1 and unicodedata.name(base, "").startswith("LATIN"):
            out.append("".join(c for c in dec if not unicodedata.combining(c)))
        else:
            out.append(ch)
    return "".join(out)


def osa(a, b):
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


class TestSpecCoverage(unittest.TestCase):
    """The registry must contain what sections 4 and 5 list."""

    @classmethod
    def setUpClass(cls):
        cls.reg = registry()

    def test_every_spec_skill_exists_with_title_aliases_and_kind(self):
        fails = []
        for sid, info in spec.SKILLS.items():
            owner = owner_of(sid)
            sk = self.reg.skill(sid)
            if sk is None:
                fails.append(f"[{owner}] {sid}: skill missing from the registry")
                continue
            if sk.title != info["title"]:
                fails.append(f"[{owner}] {sid}: title {sk.title!r} != {info['title']!r}")
            if not sk.aliases or sk.aliases[0] != info["aliases"][0]:
                fails.append(f"[{owner}] {sid}: first alias {sk.aliases[:1]} != {info['aliases'][0]!r}")
            missing = [a for a in info["aliases"] if a not in sk.aliases]
            if missing:
                fails.append(f"[{owner}] {sid}: aliases missing {missing[:4]}")
            if info["kind"] == "B" and not sk.items:
                fails.append(f"[{owner}] {sid}: must be a bank skill (items) but has none")
            if info["kind"] == "G" and sk.items:
                fails.append(f"[{owner}] {sid}: must be a generator skill but has {len(sk.items)} items")
        report(self, fails, "spec skills")

    def test_required_extras_exist(self):
        fails = []
        for sid in spec.REQUIRED_EXTRAS:
            if self.reg.skill(sid) is None:
                fails.append(f"[{owner_of(sid)}] {sid}: required extra missing")
        report(self, fails, "required extras")

    def test_extra_skills_reachable_through_own_topic(self):
        fails = []
        for sid in spec.REQUIRED_EXTRAS:
            sk = self.reg.skill(sid)
            if sk is None:
                continue
            for text in (sk.aliases[0], sk.title.lower()):
                res = self.reg.match_skills(sk.subject, text)
                if not res or res[0] != sid:
                    fails.append(f"[{owner_of(sid)}] {sid}: match_skills({sk.subject!r}, {text!r}) -> {res[:2]}")
        report(self, fails, "own-topic matching")

    def test_no_unexpected_skills_without_spec_owner(self):
        known_subjects = set(SUBJECT)
        for yr in self.reg.years():
            for s in self.reg.subjects_for_year(yr):
                self.assertIn(s.id, known_subjects, f"subject {s.id} is not in section 4")

    def test_subject_titles_orders_and_years(self):
        fails = []
        for s in spec.SUBJECTS:
            sub = self.reg.subject(s["id"])
            if sub is None:
                fails.append(f"[{s['owner']}] {s['id']}: subject missing")
                continue
            if (sub.title, sub.order) != (s["title"], s["order"]):
                fails.append(f"[{s['owner']}] {s['id']}: ({sub.title!r}, {sub.order}) != ({s['title']!r}, {s['order']})")
            if s["source"] != "frozen" and sorted(sub.years) != [10, 11]:
                fails.append(f"[{s['owner']}] {s['id']}: years {sorted(sub.years)} != [10, 11]")
        report(self, fails, "subjects")

    def test_topic_rows_and_ids(self):
        fails = []
        for s in NEW_SUBJECTS:
            owner = s["owner"]
            for year in (10, 11):
                rows = self.reg.topic_rows(s["id"], year)
                want = [tuple(lbl for lbl, _, _ in row) for row in s["rows"]]
                if rows != want:
                    fails.append(f"[{owner}] {s['id']} Y{year}: rows {rows} != {want}")
                    continue
                for row in s["rows"]:
                    for label, slug, suffixes in row:
                        t = self.reg.topic_by_label(s["id"], year, label)
                        tid = f"{s['id']}.y{year}.{slug}"
                        if t is None or t.id != tid:
                            fails.append(f"[{owner}] {tid}: topic id {getattr(t, 'id', None)}")
                            continue
                        if t.level_map != (1, 2, 3, 4, 5) or t.exam:
                            fails.append(f"[{owner}] {tid}: level_map {t.level_map} exam={t.exam}")
                        want_sk = [f"{s['id']}.{x}" for x in suffixes]
                        if not set(want_sk) <= set(t.skills):
                            fails.append(f"[{owner}] {tid}: skills {t.skills} lack {want_sk}")
                        for sk_id in t.skills:
                            if self.reg.skill(sk_id) is None:
                                fails.append(f"[{owner}] {tid}: unknown skill {sk_id}")
                        # D4: at most one bank skill and one generator skill, except all-generator topics
                        kinds = [bool(self.reg.skill(x).items) for x in t.skills if self.reg.skill(x)]
                        if not all(not k for k in kinds) and (kinds.count(True) > 1 or kinds.count(False) > 1):
                            fails.append(f"[{owner}] {tid}: more than one bank or generator skill: {t.skills}")
                pp = self.reg.topic_by_label(s["id"], year, "Past paper practice")
                if pp is None or pp.id != f"{s['id']}.y{year}.past_paper" or not pp.exam or pp.level_map != (2, 3, 3, 4, 5):
                    fails.append(f"[{owner}] {s['id']} Y{year}: past paper topic wrong: {pp}")
                else:
                    union = []
                    for row in s["rows"]:
                        for label, _, _ in row:
                            for x in self.reg.topic_by_label(s["id"], year, label).skills:
                                if x not in union:
                                    union.append(x)
                    if list(pp.skills) != union:
                        fails.append(f"[{owner}] {s['id']} Y{year}: past paper skills {pp.skills} != union {tuple(union)}")
        report(self, fails, "topics")

    def test_every_required_skill_is_reachable_from_a_row(self):
        fails = []
        extras = set(spec.REQUIRED_EXTRAS) | set(spec.OPTIONAL_EXTRAS)
        for s in NEW_SUBJECTS:
            reach = set()
            for label in [lbl for row in s["rows"] for lbl, _, _ in row]:
                t = self.reg.topic_by_label(s["id"], 11, label)
                if t:
                    reach.update(t.skills)
            for sid in spec.SKILLS:
                if sid.startswith(s["id"] + ".") and sid not in extras and sid not in reach:
                    fails.append(f"[{s['owner']}] {sid}: not reachable from any row of Year 11")
        report(self, fails, "reachability")

    def test_first_alias_is_unique_and_matches_itself(self):
        """L9: >= 3 lowercase aliases; match_skills(subject, first alias)[0] == skill.id."""
        fails = []
        for s in NEW_SUBJECTS:
            firsts = Counter()
            for sk in self.reg.skills_of(s["id"]):
                owner = s["owner"]
                if len(sk.aliases) < 3:
                    fails.append(f"[{owner}] {sk.id}: only {len(sk.aliases)} alias(es)")
                if any(a != a.lower() or not a.strip() for a in sk.aliases):
                    fails.append(f"[{owner}] {sk.id}: aliases not lowercase/non-empty")
                firsts[sk.aliases[0]] += 1
                res = self.reg.match_skills(s["id"], sk.aliases[0])
                if not res or res[0] != sk.id:
                    fails.append(f"[{owner}] {sk.id}: match_skills({sk.aliases[0]!r})[0] = {res[:1]}")
            for a, n in firsts.items():
                if n > 1:
                    fails.append(f"[{s['owner']}] {s['id']}: first alias {a!r} used by {n} skills")
        report(self, fails, "aliases")

    def test_title_lengths_l8(self):
        fails = []
        for s in NEW_SUBJECTS:
            if len(s["title"]) > 18:
                fails.append(f"[{s['owner']}] {s['id']}: subject title longer than 18")
            for yr in (10, 11):
                for row in self.reg.topic_rows(s["id"], yr):
                    for lbl in row:
                        if len(lbl) > 30:
                            fails.append(f"[{s['owner']}] {s['id']}: label {lbl!r} longer than 30")
        report(self, fails, "L8")


class TestBankItems(unittest.TestCase):
    """Per item and seed checks."""

    @classmethod
    def setUpClass(cls):
        cls.reg = registry()
        cls.skills = bank_skills()

    def test_there_are_bank_skills(self):
        self.assertGreater(len(self.skills), 0, "no bank skill with items is loaded at all")

    def test_render_deterministic_json_and_display(self):
        fails = []
        for sk in self.skills:
            owner = owner_of(sk.id)
            for it in sk.items:
                for seed in SEEDS:
                    where = f"[{owner}] {it.ref} seed={seed}"
                    try:
                        p = it.render(seed)
                        if p != it.render(seed):
                            fails.append(f"{where}: not deterministic")
                            continue
                        if (p.skill_id, p.level, p.seed, p.ref) != (sk.id, it.level, seed, it.ref):
                            fails.append(f"{where}: header {(p.skill_id, p.level, p.seed, p.ref)}")
                        if problem_from_json(problem_to_json(p)) != p:
                            fails.append(f"{where}: JSON round trip differs")
                        a = p.answer
                        if a.kind == "rubric":
                            if check(a, "anything at all").status != "unmarkable":
                                fails.append(f"{where}: rubric not unmarkable")
                            continue
                        v = check(a, a.display, p.mistakes)
                        if (v.status, v.feedback) != ("correct", ""):
                            fails.append(f"{where}: display {a.display!r} judged {v.status} note={v.feedback!r}")
                        pt = perturb(a)
                        if pt and check(a, pt, p.mistakes).status == "correct":
                            fails.append(f"{where}: perturbed {pt!r} judged correct")
                        if len(p.text) > 600 or len(p.solution) > 300 or p.solution.rstrip().endswith("."):
                            fails.append(f"{where}: lengths/trailing period")
                    except Exception as e:  # noqa: BLE001
                        fails.append(f"{where}: raised {type(e).__name__}: {e}")
        report(self, fails, "rendering")

    def test_choice_items(self):
        fails = []
        for sk in self.skills:
            owner = owner_of(sk.id)
            for it in sk.items:
                if it.kind != "choice":
                    continue
                for seed in SEEDS:
                    where = f"[{owner}] {it.ref} seed={seed}"
                    p = it.render(seed)
                    a = p.answer
                    opts, c = a.value["options"], a.value["correct"]
                    n = len(opts)
                    if not 3 <= n <= 5:
                        fails.append(f"{where}: {n} options")
                        continue
                    listing = "\n".join(f"{LETTERS[i]}) {o}" for i, o in enumerate(opts))
                    if not p.text.endswith("\n\n" + listing):
                        fails.append(f"{where}: text does not end with the options in displayed order")
                    if a.display != f"{LETTERS[c]}) {opts[c]}":
                        fails.append(f"{where}: display {a.display!r}")
                    fb = {m.answer.display: m.feedback for m in p.mistakes}
                    for j, o in enumerate(opts):
                        v = check(a, LETTERS[j], p.mistakes)
                        if j == c:
                            if (v.status, v.feedback) != ("correct", ""):
                                fails.append(f"{where}: correct letter judged {v.status}")
                            if check(a, LETTERS[j].lower(), p.mistakes).status != "correct":
                                fails.append(f"{where}: lower-case correct letter not accepted")
                            if check(a, o, p.mistakes).status != "correct":
                                fails.append(f"{where}: correct option text {o!r} not accepted")
                        else:
                            vt = check(a, o, p.mistakes)
                            if vt.status == "correct":
                                fails.append(f"{where}: wrong option text {o!r} judged correct")
                            if v.status != "wrong":
                                fails.append(f"{where}: letter {LETTERS[j]} judged {v.status}")
                            want = fb.get(f"{LETTERS[j]}) {o}", "")
                            if v.feedback != want:
                                fails.append(f"{where}: letter {LETTERS[j]} feedback {v.feedback!r} != {want!r}")
        report(self, fails, "choice items")

    def test_choice_letter_variation_l10(self):
        fails = []
        for sk in self.skills:
            owner = owner_of(sk.id)
            by_n = defaultdict(Counter)
            for it in sk.items:
                if it.kind != "choice":
                    continue
                letters = []
                for seed in VARIATION_SEEDS:
                    a = it.render(seed).answer
                    letters.append(a.value["correct"])
                    by_n[len(a.value["options"])][a.value["correct"]] += 1
                if len(set(letters)) < 2:
                    fails.append(f"[{owner}] {it.ref}: correct letter takes one value over seeds 0-19")
            for n, cnt in by_n.items():
                total = sum(cnt.values())
                if total < 40:
                    continue
                for pos in range(n):
                    share = cnt[pos] / total
                    if not (0.5 / n <= share <= 1.5 / n):
                        fails.append(f"[{owner}] {sk.id}: letter {LETTERS[pos]} share {share:.2f} with n={n} outside "
                                     f"[{0.5 / n:.2f}, {1.5 / n:.2f}]")
        report(self, fails, "L10")

    def test_short_items(self):
        fails = []
        for sk in self.skills:
            owner = owner_of(sk.id)
            for it in sk.items:
                if it.kind != "short":
                    continue
                p = it.render(0)
                a = p.answer
                where = f"[{owner}] {it.ref}"
                accept, reject, form = a.value["accept"], a.value["reject"], a.form
                fb = {m.answer.display: m.feedback for m in p.mistakes}
                for x in accept:
                    v = check(a, x, p.mistakes)
                    if (v.status, v.feedback) != ("correct", ""):
                        fails.append(f"{where}: accept {x!r} judged {v.status} note={v.feedback!r}")
                disp = a.display
                if form != "case":
                    v = check(a, disp.upper(), p.mistakes)
                    if v.status != "correct":
                        fails.append(f"{where}: upper-case {disp.upper()!r} judged {v.status}")
                if form == "any" and not re.match(r"(?i)(the|a|an)\b", disp) and not disp.strip().isdigit():
                    v = check(a, "the " + disp, p.mistakes)
                    if v.status != "correct":
                        fails.append(f"{where}: 'the {disp}' judged {v.status}")
                if form in ("any", "strict"):
                    folded = fold_plain(disp)
                    other = {norm_basic(fold_plain(x)) for x in accept[1:]} | {norm_basic(fold_plain(r)) for r in reject}
                    if folded != disp and norm_basic(folded) not in other and norm_basic(folded) != norm_basic(disp):
                        v = check(a, folded, p.mistakes)
                        if (v.status, v.feedback) != ("correct", NOTE_ACCENTS(disp)):
                            fails.append(f"{where}: folded {folded!r} judged {v.status} note={v.feedback!r}")
                if form == "case" and disp.lower() != disp:
                    v = check(a, disp.lower(), p.mistakes)
                    if disp.lower() not in {x.lower() for x in reject} and \
                            (v.status, v.feedback) != ("wrong", FORM_CASE):
                        fails.append(f"{where}: lower-cased {disp.lower()!r} judged {v.status} note={v.feedback!r}")
                if form == "any":
                    nd = norm_basic(disp)
                    letters_only = nd.replace(" ", "").isalpha() and nd.isascii()
                    if letters_only and len(nd) >= 6 and len(nd.split()) <= 3:
                        i = next((k for k in range(len(nd) // 2, len(nd) - 1)
                                  if nd[k] != nd[k + 1] and nd[k] != " " and nd[k + 1] != " "), None)
                        if i is not None:
                            t = nd[:i] + nd[i + 1] + nd[i] + nd[i + 2:]
                            rn = [norm_basic(r) for r in reject]
                            an = {norm_basic(x) for x in accept}
                            if t not in rn and t not in an and all(osa(t, r) > 1 for r in rn):
                                v = check(a, t, p.mistakes)
                                notes = {f"Watch the spelling: {x}" for x in accept}
                                if v.status != "correct" or v.feedback not in notes:
                                    fails.append(f"{where}: swap {t!r} judged {v.status} note={v.feedback!r}")
                for r in reject:
                    v = check(a, r, p.mistakes)
                    if v.status != "wrong":
                        fails.append(f"{where}: reject {r!r} judged {v.status}")
                    elif r in fb and v.feedback != fb[r]:
                        fails.append(f"{where}: reject {r!r} feedback {v.feedback!r} != {fb[r]!r}")
        report(self, fails, "short items")

    def test_v1_answer_items(self):
        fails = []
        for sk in self.skills:
            owner = owner_of(sk.id)
            for it in sk.items:
                if it.kind in ("choice", "short", "rubric"):
                    continue
                for seed in SEEDS:
                    p = it.render(seed)
                    for near in helpers.boundary_variants(p.answer):
                        if check(p.answer, near).status == "correct":
                            fails.append(f"[{owner}] {it.ref}: near miss {near!r} judged correct")
        report(self, fails, "v1-kind items")


class TestLint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = registry()
        cls.skills = bank_skills()

    def new_skills(self):
        return [sk for sk in self.skills if sk.subject in SUBJECT and SUBJECT[sk.subject]["source"] != "frozen"]

    def test_l1_every_question_has_an_id(self):
        fails = []
        for folder in (BANKS_DIR, PACKS_DIR):
            if not os.path.isdir(folder):
                continue
            for name in sorted(os.listdir(folder)):
                if not name.endswith(".json") or name.startswith("_"):
                    continue
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    data = json.load(f)
                sub = (data.get("subject") or {}).get("id") or data.get("subject_id") or name[:-5]
                for s in data.get("skills", []):
                    for i, q in enumerate(s.get("questions", [])):
                        if "id" not in q:
                            fails.append(f"[{owner_of(sub)}] {name} {s.get('id')} question #{i}: no id")
        report(self, fails, "L1")

    def test_banks_and_packs_folders_hold_only_json(self):
        for folder in (BANKS_DIR, PACKS_DIR):
            if os.path.isdir(folder):
                bad = [n for n in os.listdir(folder) if n.endswith(".py") or n == "__pycache__"]
                self.assertEqual(bad, [], f"{folder} must not contain .py files")

    def test_l2_minimum_sizes(self):
        fails = []
        for sk in self.new_skills():
            lv = Counter(i.level for i in sk.items)
            if len(sk.items) < 30:
                fails.append(f"[{owner_of(sk.id)}] {sk.id}: {len(sk.items)} questions (< 30)")
            low = [L for L in range(1, 6) if lv[L] < 4]
            if low:
                fails.append(f"[{owner_of(sk.id)}] {sk.id}: fewer than 4 questions at levels {low} ({dict(sorted(lv.items()))})")
        report(self, fails, "L2")

    def test_l3_choice_plus_short_at_least_85_percent(self):
        fails = []
        for sk in self.new_skills():
            n = len(sk.items)
            cs = sum(1 for i in sk.items if i.kind in ("choice", "short"))
            if cs < 0.85 * n:
                fails.append(f"[{owner_of(sk.id)}] {sk.id}: choice+short {cs}/{n}")
        report(self, fails, "L3")

    def test_l4_rubric_limits(self):
        fails = []
        for sk in self.new_skills():
            rubrics = [i for i in sk.items if i.kind == "rubric"]
            if not rubrics:
                continue
            owner = owner_of(sk.id)
            if not SUBJECT[sk.subject]["rubric"]:
                fails.append(f"[{owner}] {sk.id}: rubric items in a subject that may not use them")
            if any(i.level not in (4, 5) for i in rubrics):
                fails.append(f"[{owner}] {sk.id}: rubric items at levels {[i.level for i in rubrics if i.level not in (4, 5)]}")
            if len(rubrics) > int(0.15 * len(sk.items)):
                fails.append(f"[{owner}] {sk.id}: {len(rubrics)} rubric items > floor(0.15 x {len(sk.items)})")
        report(self, fails, "L4")

    def texts_to_vet(self, sk):
        for it in sk.items:
            p = it.render(0)
            a = p.answer
            if a.kind == "short":
                for x in a.value["accept"]:
                    yield it.ref, x, "accept"
            elif a.kind == "choice":
                for o in a.value["options"]:
                    yield it.ref, o, "option"

    def test_l5_no_distress_intent_or_cheat_text_in_answers(self):
        fails = []
        for sk in self.new_skills():
            for ref, text, what in self.texts_to_vet(sk):
                if is_distress(text) or is_cheat_request(text) or intent(text) is not None:
                    why = "distress" if is_distress(text) else ("cheat" if is_cheat_request(text) else intent(text))
                    fails.append(f"[{owner_of(sk.id)}] {ref}: {what} {text!r} is {why}")
        report(self, fails, "L5")

    def test_l6_no_accept_equals_a_label_or_button(self):
        def dash(s):
            return re.sub(r"\s+", " ", s.casefold().replace("–", "-").replace("—", "-")).strip()
        buttons = {dash(x) for x in ("Past paper practice", "My own topic", "🎓 Change year", "📘 Change subject",
                                     "A", "B", "C", "D", "E")}
        buttons |= {dash(f"Year {y}") for y in range(1, 14)} | {dash(t) for t in helpers.SUBJECT_TITLES_10_11}
        fails = []
        for sk in self.new_skills():
            labels = {dash(lbl) for yr in (10, 11) for row in self.reg.topic_rows(sk.subject, yr) for lbl in row}
            bad = labels | buttons
            for it in sk.items:
                a = it.render(0).answer
                if a.kind != "short":
                    continue
                for x in a.value["accept"]:
                    if dash(x) in bad:
                        fails.append(f"[{owner_of(sk.id)}] {it.ref}: accept {x!r} equals a topic label or button text")
        report(self, fails, "L6")

    def test_l7_no_markdown_or_latex(self):
        fails = []
        pat = re.compile(r"\*\*|`|\$|\\")

        def bad(t):
            return bool(pat.search(t)) or any(line.startswith("#") for line in t.splitlines())

        for sk in self.new_skills():
            for it in sk.items:
                p = it.render(0)
                parts = [p.text, p.solution, p.hint] + [m.feedback for m in p.mistakes]
                if p.answer.kind == "choice":
                    parts += list(p.answer.value["options"])
                if p.answer.kind == "rubric":
                    parts += [p.answer.display, p.answer.mark_scheme]
                for t in parts:
                    if bad(t):
                        fails.append(f"[{owner_of(sk.id)}] {it.ref}: markdown/LaTeX in {t[:60]!r}")
        report(self, fails, "L7")

    def test_l11_scripts(self):
        arabic = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
        hanzi = re.compile(r"[一-鿿㐀-䶿]")
        cyr = re.compile(r"[Ѐ-ӿ]")
        fails = []
        for sk in self.new_skills():
            owner = owner_of(sk.id)
            if sk.subject in ("arabic", "mandarin"):
                for it in sk.items:
                    a = it.render(0).answer
                    if a.kind == "short":
                        for x in a.value["accept"]:
                            if arabic.search(x) or hanzi.search(x):
                                fails.append(f"[{owner}] {it.ref}: accept {x!r} contains Arabic script or hanzi")
            if sk.subject == "russian":
                n = sum(1 for it in sk.items if it.kind == "short"
                        and any(cyr.search(x) for x in it.render(0).answer.value["accept"]))
                if n > 0.3 * len(sk.items):
                    fails.append(f"[{owner}] {sk.id}: {n}/{len(sk.items)} Cyrillic short answers (> 30%)")
        report(self, fails, "L11")

    def test_r12_answers_are_not_commands(self):
        fails = []
        words = {"help", "hint", "skip", "pass", "next", "explain"}
        for sk in self.new_skills():
            for ref, text, what in self.texts_to_vet(sk):
                if text.strip().casefold() in words:
                    fails.append(f"[{owner_of(sk.id)}] {ref}: {what} {text!r} is a command word")
        report(self, fails, "R12")

    def test_r6_safety_words(self):
        bad = re.compile(r"\b(suicid\w*|self[- ]?harm\w*|overdos\w*|abused|bullied|nudes)\b", re.I)
        fails = []
        for sk in self.new_skills():
            for ref, text, what in self.texts_to_vet(sk):
                if bad.search(text):
                    fails.append(f"[{owner_of(sk.id)}] {ref}: {what} {text!r} contains a safety word")
        report(self, fails, "R6")

    def test_mixes(self):
        """Section 5 'Mixes' (per bank skill)."""
        fails = []
        for sk in self.new_skills():
            sub = SUBJECT[sk.subject]
            mix = sub["mix"]
            if mix is None or not sk.items:
                continue
            owner = owner_of(sk.id)
            n = len(sk.items)
            cnt = Counter(i.kind for i in sk.items)
            ch, sh, ru = cnt["choice"] / n, cnt["short"] / n, cnt["rubric"] / n
            num = (n - cnt["choice"] - cnt["short"] - cnt["rubric"]) / n
            eps = 1e-9
            where = f"[{owner}] {sk.id} ({mix}) choice={ch:.0%} short={sh:.0%} rubric={ru:.0%} number/other={num:.0%}"
            ok = True
            if mix == "M1":
                ok = 0.55 - eps <= ch <= 0.70 + eps and 0.20 - eps <= sh <= 0.35 + eps
            elif mix == "M2":
                ok = 0.55 - eps <= ch <= 0.75 + eps and 0.25 - eps <= sh <= 0.45 + eps and cnt["rubric"] == 0 and num <= 0.15 + eps
            elif mix == "M3":
                ok = 0.40 - eps <= ch <= 0.60 + eps and 0.40 - eps <= sh <= 0.60 + eps and cnt["rubric"] == 0
            elif mix == "M4":
                ok = ch >= 0.65 - eps and sh <= 0.35 + eps and cnt["rubric"] == 0
            if not ok:
                fails.append(where)
        report(self, fails, "mixes")


if __name__ == "__main__":
    unittest.main()
