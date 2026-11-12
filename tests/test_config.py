import dataclasses
import os
import tempfile
import unittest
from unittest import mock

import helpers
from tutor import config as cfg_mod
from tutor.config import Config, REPO_ROOT, load_config


class ConfigCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.missing = os.path.join(self.tmp.name, "does-not-exist.env")

    def env_file(self, text):
        path = os.path.join(self.tmp.name, ".env")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def load(self, environ=None, file_text=None):
        env = dict(environ or {})
        env["TUTOR_ENV_FILE"] = self.env_file(file_text) if file_text is not None else self.missing
        return load_config(env)


class TestDefaults(ConfigCase):
    def test_repo_root(self):
        self.assertEqual(os.path.realpath(REPO_ROOT), os.path.realpath(helpers.ROOT))
        self.assertTrue(os.path.isdir(os.path.join(REPO_ROOT, "tutor")))

    def test_defaults(self):
        c = self.load()
        self.assertIsNone(c.token)
        self.assertIsNone(c.owner_id)
        self.assertIsNone(c.anthropic_api_key)
        self.assertEqual(c.model, "claude-haiku-5-5")
        self.assertEqual(os.path.normpath(c.db_path), os.path.normpath(os.path.join(REPO_ROOT, "data", "tutor.db")))
        self.assertEqual(c.llm_daily_limit, 40)
        self.assertEqual(c.flood_per_minute, 20)

    def test_dataclass_defaults(self):
        c = Config()
        self.assertEqual((c.token, c.owner_id, c.anthropic_api_key, c.model, c.db_path, c.llm_daily_limit,
                          c.flood_per_minute), (None, None, None, "claude-haiku-5-5", ":memory:", 40, 20))

    def test_frozen(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            Config().token = "x"


class TestLookup(ConfigCase):
    def test_file_values(self):
        c = self.load(file_text="TELEGRAM_BOT_TOKEN=filetoken\nTUTOR_OWNER_ID=42\nANTHROPIC_API_KEY=k1\nTUTOR_MODEL=m1\n")
        self.assertEqual((c.token, c.owner_id, c.anthropic_api_key, c.model), ("filetoken", 42, "k1", "m1"))

    def test_env_beats_file(self):
        c = self.load({"TELEGRAM_BOT_TOKEN": "envtoken", "TUTOR_OWNER_ID": "7"},
                      "TELEGRAM_BOT_TOKEN=filetoken\nTUTOR_OWNER_ID=42\nANTHROPIC_API_KEY=fromfile\n")
        self.assertEqual((c.token, c.owner_id, c.anthropic_api_key), ("envtoken", 7, "fromfile"))

    def test_file_parsing(self):
        text = ('# TELEGRAM_BOT_TOKEN=commented\n\n   \nTUTOR_MODEL="quoted-model"\n'
                "ANTHROPIC_API_KEY='single'\nTELEGRAM_BOT_TOKEN=real\n")
        c = self.load(file_text=text)
        self.assertEqual((c.token, c.model, c.anthropic_api_key), ("real", "quoted-model", "single"))

    def test_missing_file_is_fine(self):
        self.assertIsNone(self.load().token)

    def test_default_environ_is_os_environ(self):
        with mock.patch.dict(os.environ, {"TUTOR_ENV_FILE": self.missing, "TELEGRAM_BOT_TOKEN": "from-os",
                                          "TUTOR_OWNER_ID": "5"}, clear=True):
            c = load_config()
        self.assertEqual((c.token, c.owner_id), ("from-os", 5))

    def test_does_not_mutate_input(self):
        env = {"TUTOR_ENV_FILE": self.missing, "TELEGRAM_BOT_TOKEN": "t"}
        before = dict(env)
        load_config(env)
        self.assertEqual(env, before)


class TestBot(ConfigCase):
    def test_bot_token_key_and_db(self):
        c = self.load({"BOT": "english", "TELEGRAM_BOT_TOKEN_ENGLISH": "tok-e", "TELEGRAM_BOT_TOKEN": "wrong"})
        self.assertEqual(c.token, "tok-e")
        self.assertEqual(os.path.normpath(c.db_path),
                         os.path.normpath(os.path.join(REPO_ROOT, "data", "tutor-english.db")))

    def test_bot_name_case(self):
        c = self.load({"BOT": "English", "TELEGRAM_BOT_TOKEN_ENGLISH": "tok-e"})
        self.assertEqual(c.token, "tok-e")
        self.assertTrue(c.db_path.endswith("tutor-english.db"))

    def test_bot_token_from_file(self):
        c = self.load({"BOT": "english"}, "TELEGRAM_BOT_TOKEN_ENGLISH=from-file\nTELEGRAM_BOT_TOKEN=plain\n")
        self.assertEqual(c.token, "from-file")

    def test_bot_without_its_token_has_none(self):
        c = self.load({"BOT": "english", "TELEGRAM_BOT_TOKEN": "plain"})
        self.assertIsNone(c.token)

    def test_no_bot_uses_plain_token(self):
        self.assertEqual(self.load({"TELEGRAM_BOT_TOKEN": "plain", "TELEGRAM_BOT_TOKEN_ENGLISH": "x"}).token, "plain")


class TestDbPath(ConfigCase):
    def test_relative_resolved_against_repo_root(self):
        c = self.load({"TUTOR_DB": "somewhere/x.db"})
        self.assertEqual(os.path.normpath(c.db_path), os.path.normpath(os.path.join(REPO_ROOT, "somewhere", "x.db")))
        self.assertTrue(os.path.isabs(c.db_path))

    def test_absolute_kept(self):
        p = os.path.join(self.tmp.name, "abs.db")
        self.assertEqual(self.load({"TUTOR_DB": p}).db_path, p)

    def test_tutor_db_beats_bot_default(self):
        p = os.path.join(self.tmp.name, "abs.db")
        self.assertEqual(self.load({"TUTOR_DB": p, "BOT": "english"}).db_path, p)

    def test_db_from_file(self):
        p = os.path.join(self.tmp.name, "f.db")
        self.assertEqual(self.load(file_text=f"TUTOR_DB={p}\n").db_path, p)


class TestOwnerAndLimits(ConfigCase):
    def test_owner_valid(self):
        self.assertEqual(self.load({"TUTOR_OWNER_ID": "123456789"}).owner_id, 123456789)

    def test_owner_invalid_is_none_with_warning(self):
        for bad in ("abc", "12x", "1.5", "@name"):
            with self.subTest(value=bad):
                with self.assertLogs(level="WARNING"):
                    c = self.load({"TUTOR_OWNER_ID": bad})
                self.assertIsNone(c.owner_id)

    def test_owner_missing_or_empty(self):
        self.assertIsNone(self.load().owner_id)
        self.assertIsNone(self.load({"TUTOR_OWNER_ID": ""}).owner_id)

    def test_llm_limit(self):
        self.assertEqual(self.load({"TUTOR_LLM_DAILY_LIMIT": "5"}).llm_daily_limit, 5)
        self.assertEqual(self.load({"TUTOR_LLM_DAILY_LIMIT": "0"}).llm_daily_limit, 0)
        self.assertEqual(self.load({"TUTOR_LLM_DAILY_LIMIT": "abc"}).llm_daily_limit, 40)
        self.assertEqual(self.load({"TUTOR_LLM_DAILY_LIMIT": ""}).llm_daily_limit, 40)
        self.assertEqual(self.load(file_text="TUTOR_LLM_DAILY_LIMIT=12\n").llm_daily_limit, 12)

    def test_model_override(self):
        self.assertEqual(self.load({"TUTOR_MODEL": "other-model"}).model, "other-model")


if __name__ == "__main__":
    unittest.main()
