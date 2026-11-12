"""docs/ARCHITECTURE_V2.md sections 2.1-2.3: the choice and short answer kinds, kinds.py, fingerprint."""
import hashlib
import json
import random
import unittest

import helpers
from helpers import NOTE_SPELLING, NOTE_ACCENTS, FORM_CASE, LETTERS_TEXT
from tutor.content import (Answer, Mistake, Problem, check, problem_from_json, problem_to_json, fingerprint,
                           build_choice, build_short, shuffle_order, letters_text, CHOICE_LETTERS, SHORT_FORMS,
                           NOTE_SPELLING as C_NOTE_SPELLING, NOTE_ACCENTS as C_NOTE_ACCENTS,
                           FORM_CASE as C_FORM_CASE)

OPTIONS = ["Nucleus", "Mitochondria", "Ribosome", "Cell membrane"]
FB_A = "The nucleus stores the DNA"


def choice_answer(options=OPTIONS, correct=1):
    return Answer("choice", f"{'ABCDE'[correct]}) {options[correct]}", {"options": list(options), "correct": correct})


def choice_mistakes(options=OPTIONS, fb=((0, FB_A),)):
    return tuple(Mistake(Answer("choice", f"{'ABCDE'[j]}) {options[j]}", {"options": list(options), "correct": j}), f)
                 for j, f in fb)


def short_answer(accept, reject=(), form="any"):
    return Answer("short", accept[0], {"accept": list(accept), "reject": list(reject)}, form=form)


def short_mistakes(feedback, form="any"):
    return tuple(Mistake(Answer("short", r, {"accept": [r], "reject": []}, form=form), fb) for r, fb in feedback.items())


class TestConstants(unittest.TestCase):
    def test_exports_and_strings(self):
        self.assertEqual(CHOICE_LETTERS, "ABCDE")
        self.assertEqual(tuple(SHORT_FORMS), ("any", "strict", "case", "pinyin"))
        self.assertEqual(C_NOTE_SPELLING, "Watch the spelling: {answer}")
        self.assertEqual(C_NOTE_ACCENTS, "Watch the accents: {answer}")
        self.assertEqual(C_FORM_CASE, helpers.FORM_CASE)
        self.assertEqual(NOTE_SPELLING("x"), "Watch the spelling: x")


class TestChoiceTable(unittest.TestCase):
    """Acceptance table: choice (section 2.3)."""
    ans = choice_answer()
    mist = choice_mistakes()

    CORRECT_INPUTS = ["B", "b", "(b)", "B)", "b.", "[B]", "B!", "B ✅", "answer: B", "Answer - b", "the answer is B",
                      "it's B", "I think it's b", "option B", "B) Mitochondria", "b - mitochondria", "B mitochondria",
                      "Mitochondria", "the mitochondria", "MITOCHONDRIA", "B because it releases energy",
                      "I think it's\nB", "B\nbecause that's where respiration happens"]
    WRONG_FB = ["A", "a", "Nucleus", "A) Nucleus"]
    WRONG_PLAIN = ["(c)", "answer: D", "cell membrane"]
    UNPARSED = ["", "E", "B or C", "B and C", "B, C", "B/C", "B) Nucleus", "B\nactually C", "mitochondrion", "2",
                "what is a ribosome?"]

    def test_correct(self):
        for t in self.CORRECT_INPUTS:
            with self.subTest(text=t):
                v = check(self.ans, t, self.mist)
                self.assertEqual((v.status, v.feedback), ("correct", ""))

    def test_wrong_with_feedback(self):
        for t in self.WRONG_FB:
            with self.subTest(text=t):
                v = check(self.ans, t, self.mist)
                self.assertEqual((v.status, v.feedback), ("wrong", FB_A))

    def test_wrong_plain(self):
        for t in self.WRONG_PLAIN:
            with self.subTest(text=t):
                self.assertEqual(check(self.ans, t, self.mist).status, "wrong")

    def test_unparsed(self):
        for t in self.UNPARSED:
            with self.subTest(text=t):
                self.assertEqual(check(self.ans, t, self.mist).status, "unparsed")

    def test_display_is_correct_without_note(self):
        v = check(self.ans, self.ans.display)
        self.assertEqual((v.status, v.feedback), ("correct", ""))

    def test_no_typo_tolerance(self):
        for t in ("mitochondira", "mitochondrian", "Mitocondria"):
            with self.subTest(text=t):
                self.assertNotEqual(check(self.ans, t).status, "correct")

    def test_valid_letters_follow_option_count(self):
        three = choice_answer(["Red", "Green", "Blue"], 2)
        self.assertEqual(check(three, "C").status, "correct")
        self.assertEqual(check(three, "A").status, "wrong")
        self.assertEqual(check(three, "D").status, "unparsed")        # beyond n -> invalid
        self.assertEqual(check(three, "E").status, "unparsed")
        five = choice_answer(["a1", "b2", "c3", "d4", "e5"], 4)
        self.assertEqual(check(five, "E").status, "correct")
        self.assertEqual(check(five, "(e)").status, "correct")

    def test_conflict_between_letter_and_other_option(self):
        # (b) rest R equals a different option -> conflict -> unparsed
        self.assertEqual(check(self.ans, "B) Nucleus").status, "unparsed")
        self.assertEqual(check(self.ans, "A - Mitochondria").status, "unparsed")

    def test_letter_with_unrelated_rest_is_the_letter(self):
        # (b): R matches no option -> the letter
        self.assertEqual(check(self.ans, "B) the powerhouse").status, "correct")
        self.assertEqual(check(self.ans, "A) the powerhouse").status, "wrong")

    def test_bottom_up_reading(self):
        self.assertEqual(check(self.ans, "A\nB").status, "unparsed")      # two distinct letters named
        self.assertEqual(check(self.ans, "working it out\nB").status, "correct")

    def test_filler_requires_whole_words(self):
        self.assertEqual(check(self.ans, "I choose B").status, "correct")
        self.assertEqual(check(self.ans, "I'll go with b").status, "correct")
        self.assertEqual(check(self.ans, "letter B").status, "correct")
        self.assertEqual(check(self.ans, "going with B").status, "correct")
        self.assertEqual(check(self.ans, "I pick B").status, "correct")

    def test_subscript_and_quotes_normalised(self):
        opts = ["CO₂", "H₂O", "O₂"]
        a = choice_answer(opts, 1)
        self.assertEqual(check(a, "H2O").status, "correct")
        self.assertEqual(check(a, "H₂O").status, "correct")

    def test_apostrophe_options(self):
        opts = ["Parkinson’s disease", "Alzheimer's disease", "Huntington's disease"]
        a = choice_answer(opts, 1)
        self.assertEqual(check(a, "alzheimers disease").status, "correct")
        self.assertEqual(check(a, "Alzheimer’s disease").status, "correct")


SHORT_ROWS = [
    # (accept, reject, form, feedback, correct, notes {input: note}, wrong, wrong_fb {input: fb}, unparsed)
    dict(name="photosynthesis", accept=["photosynthesis"], reject=["respiration"], form="any", fb={"respiration": "fbR"},
         C=["photosynthesis", "Photosynthesis.", "PHOTOSYNTHESIS", "it's photosynthesis", "the answer is photosynthesis",
            "answer: photosynthesis", "I think it's photosynthesis", "it's called photosynthesis",
            "photosynthesis because light is absorbed", '"photosynthesis"', "photosynthesis 😊"],
         N={"photosinthesis": NOTE_SPELLING("photosynthesis"), "photosynthesys": NOTE_SPELLING("photosynthesis")},
         W=["chlorophyll", "glucose", "fotosynthesis"], WF={"respiration": "fbR", "Respiration.": "fbR"},
         U=["", "what does photosynthesis mean?", "photosynthesis and respiration",
            "the plant uses light energy from the sun to make its own food", "can you explain"]),
    dict(name="alkane", accept=["alkane"], reject=["alkene"], form="any", fb={},
         C=["alkane", "an alkane"], N={"alkanes": NOTE_SPELLING("alkane"), "alkaen": NOTE_SPELLING("alkane")},
         W=["alkene"], WF={}, U=[]),
    dict(name="bibliotheque", accept=["la bibliothèque"], reject=["la librairie", "le bibliothèque"], form="strict",
         fb={"la librairie": "fbL", "le bibliothèque": "fbG"},
         C=["la bibliothèque", "La Bibliothèque", "la bibliothèque."],
         N={"la bibliotheque": NOTE_ACCENTS("la bibliothèque"), "LA BIBLIOTHEQUE": NOTE_ACCENTS("la bibliothèque")},
         W=["bibliothèque", "la bibliotek"], WF={"la librairie": "fbL", "le bibliothèque": "fbG", "le bibliotheque": "fbG"},
         U=["", "c'est la bibliothèque"]),
    dict(name="madchen", accept=["das Mädchen"], reject=[], form="strict", fb={},
         C=["das Mädchen", "Das Mädchen"],
         N={"das Madchen": NOTE_ACCENTS("das Mädchen"), "das Maedchen": NOTE_ACCENTS("das Mädchen")},
         W=["die Mädchen", "Mädchen"], WF={}, U=[]),
    dict(name="co2", accept=["CO2"], reject=[], form="case", fb={},
         C=["CO2", "CO₂", "C O 2"], N={}, W=["CO", "O2"], WF={"co2": helpers.FORM_CASE, "Co2": helpers.FORM_CASE}, U=[""]),
    dict(name="pinyin", accept=["nǐ hǎo"], reject=[], form="pinyin", fb={},
         C=["nǐ hǎo", "ni hao", "nihao", "ni3 hao3", "Ni Hao"], N={}, W=["zai jian", "xie xie"], WF={}, U=[""]),
    dict(name="year", accept=["1918"], reject=[], form="any", fb={},
         C=["1918", "in 1918", "It ended in 1918.", "11 November 1918"], N={}, W=["1917", "1919", "1914-1918"], WF={},
         U=[""]),
    dict(name="binary", accept=["00101101", "0010 1101"], reject=[], form="any", fb={},
         C=["00101101", "0010 1101"], N={}, W=["101101", "00101100"], WF={}, U=[""]),
]


class TestCapitalLetterOptions(unittest.TestCase):
    """Options such as 'C minor' must not be read as the letter answer C."""
    OPTS = ["A major", "D major", "C minor", "G major"]
    ans = choice_answer(OPTS, 1)

    def test_option_texts(self):
        self.assertEqual(check(self.ans, "D major").status, "correct")
        self.assertEqual(check(self.ans, "d major").status, "correct")
        self.assertEqual(check(self.ans, "C minor").status, "wrong")
        self.assertEqual(check(self.ans, "A major").status, "wrong")
        self.assertEqual(check(self.ans, "G major").status, "wrong")

    def test_letters_still_work(self):
        self.assertEqual(check(self.ans, "B").status, "correct")
        self.assertEqual(check(self.ans, "d").status, "wrong")           # displayed letter D is "G major"
        self.assertEqual(check(self.ans, "C").status, "wrong")

    def test_unicode_minus_equals_hyphen(self):
        self.assertEqual(check(Answer("number", "-18", -18.0), "\u221218").status, "correct")
        self.assertEqual(check(Answer("number", "-18", -18.0), "-18").status, "correct")
        self.assertEqual(check(short_answer(["-18"]), "\u221218").status, "correct")
        a = choice_answer(["-18", "18", "-8"], 0)
        self.assertEqual(check(a, "\u221218").status, "correct")
        self.assertEqual(check(a, "\u22128").status, "wrong")


class TestShortTable(unittest.TestCase):
    """Acceptance table: short (section 2.3). Every cell is asserted exactly."""

    def rows(self):
        for r in SHORT_ROWS:
            ans = short_answer(r["accept"], r["reject"], r["form"])
            yield r, ans, short_mistakes(r["fb"], r["form"])

    def test_correct(self):
        for r, ans, mist in self.rows():
            for t in r["C"]:
                with self.subTest(row=r["name"], text=t):
                    v = check(ans, t, mist)
                    self.assertEqual((v.status, v.feedback), ("correct", ""))

    def test_correct_with_note(self):
        for r, ans, mist in self.rows():
            for t, note in r["N"].items():
                with self.subTest(row=r["name"], text=t):
                    v = check(ans, t, mist)
                    self.assertEqual((v.status, v.feedback), ("correct", note))

    def test_wrong(self):
        for r, ans, mist in self.rows():
            for t in r["W"]:
                with self.subTest(row=r["name"], text=t):
                    self.assertEqual(check(ans, t, mist).status, "wrong")

    def test_wrong_with_feedback(self):
        for r, ans, mist in self.rows():
            for t, fb in r["WF"].items():
                with self.subTest(row=r["name"], text=t):
                    v = check(ans, t, mist)
                    self.assertEqual((v.status, v.feedback), ("wrong", fb))

    def test_unparsed(self):
        for r, ans, mist in self.rows():
            for t in r["U"]:
                with self.subTest(row=r["name"], text=t):
                    self.assertEqual(check(ans, t, mist).status, "unparsed")

    def test_display_never_gets_a_note(self):
        for r, ans, mist in self.rows():
            with self.subTest(row=r["name"]):
                v = check(ans, ans.display, mist)
                self.assertEqual((v.status, v.feedback), ("correct", ""))


class TestShortRules(unittest.TestCase):
    def test_typo_needs_six_letters(self):
        for t in ("cel", "celll", "cll"):
            with self.subTest(text=t):
                self.assertNotEqual(check_short(["cell"], t).status, "correct")
        self.assertNotEqual(check_short(["plant"], "plamt").status, "correct")      # 5 letters: not eligible

    def test_typo_first_letter_must_match(self):
        self.assertNotEqual(check_short(["photosynthesis"], "hotosynthesis").status, "correct")
        self.assertNotEqual(check_short(["mitosis"], "itosis").status, "correct")
        v = check_short(["mitosis"], "mitosiss")
        self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("mitosis")))

    def test_typo_distance_one_below_ten_two_from_ten(self):
        self.assertNotEqual(check_short(["mitosis"], "mitoxxs").status, "correct")             # 2 edits, len 7
        v = check_short(["photosynthesis"], "phtosynthesys")          # 2 edits (1 deletion, 1 substitution)
        self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("photosynthesis")))
        # section 10.2 (c): two SUBSTITUTIONS are never a typo, even in a long word
        self.assertNotEqual(check_short(["photosynthesis"], "photosinthesys").status, "correct")
        self.assertNotEqual(check_short(["photosynthesis"], "photosinthesyzz").status, "correct")   # 4 edits

    def test_typo_ten_char_accept_allows_two(self):
        v = check_short(["chromosome"], "chrmosome")           # 1 deletion
        self.assertEqual(v.status, "correct")
        v = check_short(["chromosome"], "chrmosomes")          # 2 edits
        self.assertEqual(v.status, "correct")
        self.assertNotEqual(check_short(["chromosome"], "chrmsmes").status, "correct")      # 3 edits

    def test_adjacent_swap_is_one_osa_edit(self):
        v = check_short(["mitochondria"], "mitochondira")
        self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("mitochondria")))

    def test_typo_closer_to_reject_is_not_accepted(self):
        # "meiosiss" is nearer to the reject than to the accept? both distance 1 -> not strictly smaller
        v = check_short(["mitosis"], "meiosis", reject=["meiosis"])
        self.assertEqual(v.status, "wrong")
        v = check_short(["mitosis"], "meitosis", reject=["meiosis"])
        self.assertNotEqual(v.status, "correct")

    def test_no_typo_tolerance_in_other_forms(self):
        self.assertNotEqual(check_short(["la bibliothèque"], "la bibliotheqe", form="strict").status, "correct")
        self.assertNotEqual(check_short(["Photosynthesis"], "Photosinthesis", form="case").status, "correct")
        self.assertNotEqual(check_short(["nǐ hǎo ma"], "ni hao mb", form="pinyin").status, "correct")

    def test_typo_not_for_digits_or_symbols(self):
        self.assertNotEqual(check_short(["photosynthesis"], "photosynthesis2").status, "correct")

    def test_typo_max_three_words(self):
        # accept of 4 words is not eligible
        self.assertNotEqual(check_short(["great fire of london"], "grat fire of london").status, "correct")
        self.assertEqual(check_short(["great fire london"], "grat fire london").status, "correct")

    def test_word_count_limit(self):
        self.assertEqual(check_short(["photosynthesis"], "green plants make sugar using water").status, "wrong")       # 6 words
        self.assertEqual(check_short(["photosynthesis"], "green plants make sugar using water daily").status, "unparsed")  # 7

    def test_word_count_scales_with_accept_length(self):
        a = ["the treaty of versailles ended the war"]     # 7 words -> limit 14 words
        self.assertEqual(check_short(a, "the treaty of locarno made peace between the powers in europe").status, "wrong")
        self.assertEqual(check_short(a, " ".join(["word"] * 15)).status, "unparsed")

    def test_question_is_unparsed(self):
        for t in ("what is the answer?", "photosyn?", "how do plants make food", "why", "which one is it", "does it start with p"):
            with self.subTest(text=t):
                self.assertEqual(check_short(["photosynthesis"], t).status, "unparsed")

    def test_containment_with_filler_only(self):
        a = ["photosynthesis"]
        self.assertEqual(check_short(a, "this process is called photosynthesis").status, "correct")
        self.assertEqual(check_short(a, "a kind of photosynthesis i think").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis is cool").status, "unparsed")

    def test_containment_requires_whole_words(self):
        self.assertNotEqual(check_short(["cell"], "cellular").status, "correct")
        self.assertEqual(check_short(["cell"], "the cell").status, "correct")

    def test_reason_lines_are_ignored(self):
        a = ["photosynthesis"]
        self.assertEqual(check_short(a, "photosynthesis\nbecause plants need light").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis\nsince it uses light").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis coz light").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis\nas plants need light").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis\nthis is because it uses light").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis\nthat's because it uses light").status, "correct")

    def test_answer_line_is_the_bottom_most_with_letters_or_digits(self):
        a = ["photosynthesis"]
        self.assertEqual(check_short(a, "hmm let me think\nphotosynthesis").status, "correct")
        self.assertEqual(check_short(a, "photosynthesis\n!!!").status, "correct")
        self.assertEqual(check_short(a, "!!! ???").status, "unparsed")

    def test_wrapping_quotes_and_brackets(self):
        a = ["photosynthesis"]
        for t in ('"photosynthesis"', "(photosynthesis)", "[photosynthesis]", "“photosynthesis”", "'photosynthesis'"):
            with self.subTest(text=t):
                self.assertEqual(check_short(a, t).status, "correct")

    def test_filler_phrases(self):
        a = ["osmosis"]
        for t in ("my answer is osmosis", "i believe osmosis", "i guess osmosis", "i'd say osmosis", "i would say osmosis",
                  "known as osmosis", "the word is osmosis", "the term is osmosis", "its osmosis", "it is osmosis",
                  "maybe osmosis", "probably osmosis", "definitely osmosis", "actually osmosis", "it must be osmosis",
                  "is it osmosis", "ans: osmosis", "final answer osmosis", "answer - osmosis", "i think it was osmosis"):
            with self.subTest(text=t):
                self.assertEqual(check_short(a, t).status, "correct")

    def test_article_stripping_any_not_strict(self):
        self.assertEqual(check_short(["mitochondria"], "the mitochondria").status, "correct")
        self.assertEqual(check_short(["mitochondria"], "an mitochondria").status, "correct")
        self.assertEqual(check_short(["la gare"], "gare", form="strict").status, "wrong")

    def test_punctuation_hyphen_slash_apostrophe_any(self):
        self.assertEqual(check_short(["right angled triangle"], "right-angled triangle").status, "correct")
        self.assertEqual(check_short(["on off"], "on/off").status, "correct")
        self.assertEqual(check_short(["parkinsons disease"], "Parkinson's disease").status, "correct")

    def test_decimal_numbers_kept(self):
        self.assertEqual(check_short(["3.14"], "3.14").status, "correct")
        self.assertEqual(check_short(["1/2"], "1/2").status, "correct")
        self.assertEqual(check_short(["-5"], "-5").status, "correct")

    def test_numeric_answers_other_big_number_is_wrong(self):
        a = ["1918"]
        self.assertEqual(check_short(a, "1918 or 1919").status, "wrong")
        self.assertEqual(check_short(a, "18 November 1918").status, "correct")
        self.assertEqual(check_short(a, "nineteen eighteen").status, "wrong")

    def test_equal_accepts_and_second_accept(self):
        a = ["World War Two", "Second World War", "WW2"]
        for t in a:
            with self.subTest(text=t):
                self.assertEqual(check_short(a, t).status, "correct")
        self.assertEqual(check_short(a, "second world war").status, "correct")

    def test_german_fold_variant_only_on_any_strict(self):
        self.assertEqual(check_short(["schön"], "schoen", form="strict").status, "correct")
        self.assertEqual(check_short(["schön"], "schon", form="strict").status, "correct")
        self.assertEqual(check_short(["über"], "ueber").feedback, NOTE_ACCENTS("über"))
        self.assertEqual(check_short(["straße"], "strasse").feedback, NOTE_ACCENTS("straße"))

    def test_cyrillic_yo_folds_without_note(self):
        v = check_short(["всё"], "все", form="strict")
        self.assertEqual((v.status, v.feedback), ("correct", ""))

    def test_cyrillic_short_i_is_not_folded(self):
        self.assertNotEqual(check_short(["май"], "маи", form="strict").status, "correct")

    def test_pinyin_never_adds_note(self):
        for t in ("ni hao", "Ni3 hao3", "nǐhǎo", "ni-hao", "ni'hao"):
            with self.subTest(text=t):
                v = check_short(["nǐ hǎo"], t, form="pinyin")
                self.assertEqual((v.status, v.feedback), ("correct", ""))

    def test_pinyin_umlaut_u_folds(self):
        self.assertEqual(check_short(["nǚ"], "nu", form="pinyin").status, "correct")

    def test_case_form_keeps_case_and_brackets(self):
        a = ["Ca(OH)2"]
        self.assertEqual(check_short(a, "Ca(OH)2", form="case").status, "correct")
        self.assertEqual(check_short(a, "Ca (OH) 2", form="case").status, "correct")
        v = check_short(a, "ca(oh)2", form="case")
        self.assertEqual((v.status, v.feedback), ("wrong", helpers.FORM_CASE))
        self.assertEqual(check_short(["Na+"], "Na+", form="case").status, "correct")
        self.assertEqual(check_short(["Na+"], "Na-", form="case").status, "wrong")

    def test_case_form_superscript_charge(self):
        self.assertEqual(check_short(["Na+"], "Na⁺", form="case").status, "correct")
        self.assertEqual(check_short(["Cl-"], "Cl⁻", form="case").status, "correct")

    def test_reject_beats_containment_and_folding(self):
        v = check_short(["le chat"], "le chât", reject=["le chât"], form="strict")
        self.assertEqual(v.status, "wrong")

    def test_curly_quotes_and_apostrophes(self):
        self.assertEqual(check_short(["c'est"], "c’est", form="strict").status, "correct")

    def test_filler_words_only_unparsed_or_wrong_never_correct(self):
        self.assertNotEqual(check_short(["photosynthesis"], "the").status, "correct")
        self.assertNotEqual(check_short(["photosynthesis"], "it is").status, "correct")

    def test_v1_kinds_never_return_a_note(self):
        a = Answer("number", "5", 5.0)
        for t in ("5", "5.0", "answer: 5"):
            v = check(a, t)
            self.assertEqual((v.status, v.feedback), ("correct", ""))


def check_short(accept, text, reject=(), form="any"):
    return check(short_answer(accept, reject, form), text)


class TestBuildChoice(unittest.TestCase):
    STEM = "Which organelle releases energy by respiration?  "

    def test_shuffle_order_formula(self):
        for n in (3, 4, 5):
            for seed in range(25):
                exp = list(range(n))
                random.Random(f"choice:{seed}").shuffle(exp)
                self.assertEqual(shuffle_order(n, seed), exp)
                self.assertEqual(sorted(shuffle_order(n, seed)), list(range(n)))

    def test_shuffle_order_salt(self):
        self.assertEqual(shuffle_order(4, 3, ""), shuffle_order(4, 3))
        self.assertEqual(shuffle_order(4, 3, "a.b#c1"), shuffle_order(4, 3, "a.b#c1"))
        self.assertEqual(sorted(shuffle_order(5, 3, "a.b#c1")), list(range(5)))
        self.assertGreater(len({tuple(shuffle_order(4, 3, f"a.b#c{i}")) for i in range(30)}), 5)

    def test_shuffle_order_deterministic_and_varied(self):
        self.assertEqual(shuffle_order(4, 3), shuffle_order(4, 3))
        self.assertGreater(len({tuple(shuffle_order(4, s)) for s in range(30)}), 5)

    def test_letters_text(self):
        self.assertEqual(letters_text(3), "A, B or C")
        self.assertEqual(letters_text(4), "A, B, C or D")
        self.assertEqual(letters_text(5), "A, B, C, D or E")
        for n in (3, 4, 5):
            self.assertEqual(letters_text(n), LETTERS_TEXT(n))

    def test_text_layout_answer_and_mistakes(self):
        fb = [FB_A, None, None, "A ribosome makes protein"]
        for seed in range(30):
            text, ans, mist = build_choice(self.STEM, OPTIONS, 1, seed, fb)
            order = shuffle_order(4, seed)
            shown = [OPTIONS[i] for i in order]
            c = order.index(1)
            self.assertEqual(text, self.STEM.rstrip() + "\n\n" + "\n".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(shown)))
            self.assertEqual(ans, Answer("choice", f"{'ABCD'[c]}) Mitochondria", {"options": shown, "correct": c}))
            exp = tuple(Mistake(Answer("choice", f"{'ABCD'[j]}) {shown[j]}", {"options": shown, "correct": j}), f)
                        for j, f in enumerate([fb[i] for i in order]) if f)
            self.assertEqual(mist, exp)
            self.assertEqual(len(mist), 2)

    def test_deterministic(self):
        self.assertEqual(build_choice(self.STEM, OPTIONS, 1, 7), build_choice(self.STEM, OPTIONS, 1, 7))

    def test_without_feedback_no_mistakes(self):
        _, _, mist = build_choice(self.STEM, OPTIONS, 2, 0)
        self.assertEqual(mist, ())
        _, _, mist = build_choice(self.STEM, OPTIONS, 2, 0, [None, None, None, None])
        self.assertEqual(mist, ())

    def test_built_answer_is_marked_correctly(self):
        for seed in range(12):
            text, ans, mist = build_choice(self.STEM, OPTIONS, 1, seed, [FB_A, None, None, None])
            self.assertEqual(check(ans, ans.display, mist).status, "correct")
            letter = ans.display[0]
            for j, L in enumerate("ABCD"):
                v = check(ans, L, mist)
                self.assertEqual(v.status, "correct" if L == letter else "wrong")
            nucleus = "ABCD"[ans.value["options"].index("Nucleus")]
            self.assertEqual(check(ans, nucleus, mist).feedback, FB_A)

    def test_three_and_five_options(self):
        t3, a3, _ = build_choice("Pick one", ["Red", "Green", "Blue"], 0, 4)
        self.assertEqual(len(a3.value["options"]), 3)
        self.assertIn("\nC) ", t3)
        self.assertNotIn("\nD) ", t3)
        t5, a5, _ = build_choice("Pick one", ["a1", "b2", "c3", "d4", "e5"], 4, 4)
        self.assertIn("\nE) ", t5)

    def test_correct_letter_varies(self):
        letters = {build_choice(self.STEM, OPTIONS, 1, s)[1].display[0] for s in range(20)}
        self.assertGreaterEqual(len(letters), 2)

    def test_value_errors(self):
        bad = {
            "two options": (["A1", "B1"], 0, None),
            "six options": ([f"opt{i}" for i in range(6)], 0, None),
            "correct out of range": (OPTIONS, 4, None),
            "correct negative": (OPTIONS, -1, None),
            "duplicate options": (["Nucleus", "nucleus", "Ribosome"], 0, None),
            "duplicate after folding": (["Café", "Cafe", "Tea"], 0, None),
            "empty option": (["Nucleus", "", "Ribosome"], 0, None),
            "long option": (["Nucleus", "x" * 121, "Ribosome"], 0, None),
            "newline in option": (["Nucleus", "Two\nlines", "Ribosome"], 0, None),
            "all of the above": (["Nucleus", "Ribosome", "All of the above"], 0, None),
            "none of these": (["Nucleus", "Ribosome", "None of these"], 0, None),
            "both of the above": (["Nucleus", "Ribosome", "Both of the above"], 0, None),
            "refers to letters": (["Nucleus", "Ribosome", "A and B"], 0, None),
            "refers to letters comma": (["Nucleus", "Ribosome", "B, C"], 0, None),
            "lone letter": (["A", "Ribosome", "Cell wall"], 0, None),
            "lone letter bracket": (["(b)", "Ribosome", "Cell wall"], 0, None),
            "letter prefix": (["A) Nucleus", "Ribosome", "Cell wall"], 0, None),
            "feedback wrong length": (OPTIONS, 1, [None, None]),
            "feedback on correct": (OPTIONS, 1, [None, "no", None, None]),
            "empty feedback string": (OPTIONS, 1, ["", None, None, None]),
        }
        for name, (opts, correct, fb) in bad.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    build_choice("Stem?", opts, correct, 0, fb)


class TestBuildShort(unittest.TestCase):
    def test_answer_and_mistakes(self):
        ans, mist = build_short(["photosynthesis"], ["respiration", "digestion"], "any", {"respiration": "fbR"})
        self.assertEqual(ans, Answer("short", "photosynthesis", {"accept": ["photosynthesis"],
                                                                  "reject": ["respiration", "digestion"]}, form="any"))
        self.assertEqual(mist, (Mistake(Answer("short", "respiration", {"accept": ["respiration"], "reject": []}, form="any"),
                                        "fbR"),))
        self.assertEqual(check(ans, "respiration", mist).feedback, "fbR")

    def test_defaults(self):
        ans, mist = build_short(["Osmosis", "osmosis diffusion"])
        self.assertEqual((ans.kind, ans.display, ans.form), ("short", "Osmosis", "any"))
        self.assertEqual(ans.value, {"accept": ["Osmosis", "osmosis diffusion"], "reject": []})
        self.assertEqual(mist, ())

    def test_forms(self):
        for f in ("any", "strict", "case", "pinyin"):
            ans, _ = build_short(["x1"], form=f)
            self.assertEqual(ans.form, f)

    def test_feedback_for_each_reject_with_feedback_in_order(self):
        _, mist = build_short(["alkane"], ["alkene", "alkyne"], "any", {"alkyne": "two", "alkene": "one"})
        self.assertEqual({m.answer.display: m.feedback for m in mist}, {"alkene": "one", "alkyne": "two"})
        self.assertEqual([m.answer.display for m in mist], ["alkene", "alkyne"])        # in reject order

    def test_value_errors(self):
        cases = {
            "empty accept": dict(accept=[]),
            "empty string accept": dict(accept=[""]),
            "punctuation-only accept": dict(accept=["..."]),
            "accept too long": dict(accept=["x" * 81]),
            "reject equals accept": dict(accept=["alkane"], reject=["Alkane"]),
            "reject equals accept folded": dict(accept=["café"], reject=["cafe"], form="strict"),
            "bad form": dict(accept=["alkane"], form="fuzzy"),
            "feedback key not in reject": dict(accept=["alkane"], reject=["alkene"], feedback={"alkyne": "x"}),
            "empty feedback": dict(accept=["alkane"], reject=["alkene"], feedback={"alkene": ""}),
        }
        for name, kw in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    build_short(**kw)

    def test_duplicates_after_normalisation_allowed(self):
        ans, _ = build_short(["Osmosis", "osmosis"])
        self.assertEqual(ans.display, "Osmosis")


class TestJsonAndFingerprint(unittest.TestCase):
    def mk(self, ref="bio.cells#c01", answer=None):
        return Problem("bio.cells", 2, 5, "Q?", answer or choice_answer(), "sol", "hint",
                       choice_mistakes(), ref=ref)

    def test_round_trip_choice_short_with_ref(self):
        for a, m in ((choice_answer(), choice_mistakes()),
                     (short_answer(["alkane"], ["alkene"]), short_mistakes({"alkene": "fb"}))):
            p = Problem("x.y", 3, 9, "Q?", a, "sol", "hint", m, ref="x.y#q1")
            q = problem_from_json(problem_to_json(p))
            self.assertEqual(q, p)
            self.assertEqual(q.ref, "x.y#q1")
            self.assertEqual(json.loads(problem_to_json(p))["ref"], "x.y#q1")

    def test_ref_defaults_empty_and_v1_json_loads(self):
        p = Problem("a.b", 1, 1, "Q", Answer("number", "2", 2.0), "s", "h")
        self.assertEqual(p.ref, "")
        d = json.loads(problem_to_json(p))
        del d["ref"]
        self.assertEqual(problem_from_json(json.dumps(d)).ref, "")

    def test_fingerprint_with_ref(self):
        self.assertEqual(fingerprint(self.mk()), "bio.cells#c01")

    def test_fingerprint_without_ref_is_text_hash(self):
        p = Problem("a.b", 1, 1, "  What  is\n2+2? ", Answer("number", "4", 4.0), "s", "h")
        exp = "t:" + hashlib.sha1(" ".join(p.text.split()).casefold().encode()).hexdigest()[:16]
        self.assertEqual(fingerprint(p), exp)
        q = Problem("a.b", 5, 99, "what is 2+2?", Answer("number", "4", 4.0), "s", "h")
        self.assertEqual(fingerprint(q), exp)                 # level, seed and case do not matter
        r = Problem("a.b", 1, 1, "What is 2+3?", Answer("number", "5", 5.0), "s", "h")
        self.assertNotEqual(fingerprint(r), exp)
        self.assertEqual(len(exp), 2 + 16)


if __name__ == "__main__":
    unittest.main()
