import os
import re
import subprocess
import sys
import tempfile
import unittest

import helpers
from helpers import CODE_RE, send, CODE_OK

ROOT = helpers.ROOT
SCRUB = ("BOT", "TELEGRAM_BOT_TOKEN", "TUTOR_OWNER_ID", "ANTHROPIC_API_KEY", "TUTOR_MODEL", "TUTOR_DB",
         "TUTOR_LLM_DAILY_LIMIT", "TUTOR_ENV_FILE")


class CliCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "cli.db")
        self.env = {k: v for k, v in os.environ.items() if k not in SCRUB and not k.startswith("TELEGRAM_BOT_TOKEN_")}
        self.env["TUTOR_DB"] = self.db
        self.env["TUTOR_ENV_FILE"] = os.path.join(self.tmp.name, "no-such.env")
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def run_cli(self, *args, env_extra=None):
        env = dict(self.env)
        env.update(env_extra or {})
        return subprocess.run([sys.executable, "-m", "tutor", *args], cwd=ROOT, env=env, capture_output=True,
                              text=True, timeout=60)


class TestCodesCommand(CliCase):
    def test_codes_3(self):
        r = self.run_cli("codes", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertRegex(line, CODE_RE)
        self.assertEqual(len(set(lines)), 3)
        self.assertTrue(os.path.exists(self.db))

    def test_codes_are_redeemable_via_engine_on_same_db(self):
        from tutor.config import Config
        from tutor.db import Store
        from tutor.engine import Engine
        r = self.run_cli("codes", "2")
        codes = r.stdout.split()
        self.assertEqual(len(codes), 2)
        store = Store(self.db)
        self.addCleanup(store.close)
        self.assertEqual(store.count_unused_codes(), 2)
        engine = Engine(store, Config(owner_id=999, db_path=self.db), registry=helpers.shared_registry(), llm=None)
        self.assertEqual(send(engine, 5, codes[0].lower())[0].text, CODE_OK)
        self.assertEqual(send(engine, 6, codes[0])[0].text, helpers.CODE_BAD)
        self.assertEqual(send(engine, 6, codes[1])[0].text, CODE_OK)

    def test_two_runs_give_different_codes(self):
        a = self.run_cli("codes", "5").stdout.split()
        b = self.run_cli("codes", "5").stdout.split()
        self.assertFalse(set(a) & set(b))

    def test_codes_1_and_1000(self):
        r = self.run_cli("codes", "1")
        self.assertEqual((r.returncode, len(r.stdout.splitlines())), (0, 1))
        r = self.run_cli("codes", "1000")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 1000)
        self.assertEqual(len(set(lines)), 1000)

    def test_bad_n_exits_2(self):
        for bad in ("0", "1001", "abc", "-5", "2.5", ""):
            with self.subTest(n=bad):
                r = self.run_cli("codes", bad)
                self.assertEqual(r.returncode, 2, (bad, r.stdout, r.stderr))
                self.assertEqual(r.stdout.strip(), "")
                self.assertTrue(r.stderr.strip())

    def test_missing_n_exits_2(self):
        r = self.run_cli("codes")
        self.assertEqual(r.returncode, 2)

    def test_needs_no_token_and_no_network(self):
        r = self.run_cli("codes", "1", env_extra={"HTTPS_PROXY": "http://127.0.0.1:9", "HTTP_PROXY": "http://127.0.0.1:9"})
        self.assertEqual(r.returncode, 0, r.stderr)


class TestTokenErrors(CliCase):
    def test_check_without_token(self):
        r = self.run_cli("--check")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Set TELEGRAM_BOT_TOKEN", r.stdout + r.stderr)

    def test_run_without_token_exits_1(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 1)
        self.assertIn("Set TELEGRAM_BOT_TOKEN", r.stdout + r.stderr)

    def test_message_names_the_actual_key_for_named_bot(self):
        r = self.run_cli("--check", env_extra={"BOT": "english"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("TELEGRAM_BOT_TOKEN_ENGLISH", r.stdout + r.stderr)


class TestSample(CliCase):
    def test_sample_ok(self):
        r = self.run_cli("sample", "maths.pythagoras", "2", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip())

    def test_sample_defaults(self):
        r = self.run_cli("sample", "maths.percentages")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip())

    def test_sample_is_deterministic(self):
        a = self.run_cli("sample", "physics.ohms_law", "3", "2")
        b = self.run_cli("sample", "physics.ohms_law", "3", "2")
        self.assertEqual(a.returncode, 0)
        self.assertEqual(a.stdout, b.stdout)

    def test_sample_prints_more_for_bigger_n(self):
        one = self.run_cli("sample", "maths.ratio", "1", "1").stdout
        five = self.run_cli("sample", "maths.ratio", "1", "5").stdout
        self.assertGreater(len(five), len(one))

    def test_unknown_skill_exits_2_and_lists_ids(self):
        r = self.run_cli("sample", "maths.nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("maths.pythagoras", r.stderr)
        self.assertIn("physics.ohms_law", r.stderr)


if __name__ == "__main__":
    unittest.main()
