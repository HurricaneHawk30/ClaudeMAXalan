"""Configuration: environment first, then the .env file."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Mapping

log = logging.getLogger(__name__)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class Config:
    token: str | None = None
    owner_id: int | None = None
    anthropic_api_key: str | None = None
    model: str = "claude-haiku-5-5"
    db_path: str = ":memory:"
    llm_daily_limit: int = 40
    flood_per_minute: int = 20
    llm_global_daily_limit: int = 1000
    llm_marking: bool = False          # TUTOR_LLM_MARKING: the LLM marks rubric (extended practice) answers


_TRUE = frozenset({"1", "true", "yes", "on"})


def _read_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def token_env_name(environ: Mapping[str, str] | None = None) -> str:
    """Name of the env key that holds the bot token (depends on BOT=<name>)."""
    environ = os.environ if environ is None else environ
    bot = (environ.get("BOT") or "").strip()
    return "TELEGRAM_BOT_TOKEN" + (f"_{bot.upper()}" if bot else "")


def load_config(environ: Mapping[str, str] | None = None) -> Config:
    environ = os.environ if environ is None else environ
    env_file = environ.get("TUTOR_ENV_FILE") or os.path.join(REPO_ROOT, ".env")
    file_values = _read_env_file(env_file)

    def get(key: str) -> str | None:
        value = environ.get(key)
        if value is None or value == "":
            value = file_values.get(key)
        if value is None or value == "":
            return None
        return value

    bot = (get("BOT") or "").strip()
    token = get(token_env_name({"BOT": bot}) if bot else "TELEGRAM_BOT_TOKEN")

    owner_id = None
    raw_owner = get("TUTOR_OWNER_ID")
    if raw_owner is not None:
        try:
            owner_id = int(raw_owner.strip())
        except ValueError:
            log.warning("TUTOR_OWNER_ID is not a valid integer; owner commands are disabled")

    raw_db = get("TUTOR_DB")
    if raw_db:
        db_path = raw_db
    elif bot:
        db_path = os.path.join("data", f"tutor-{bot.lower()}.db")
    else:
        db_path = os.path.join("data", "tutor.db")
    if db_path != ":memory:" and not os.path.isabs(db_path):
        db_path = os.path.join(REPO_ROOT, db_path)

    def int_setting(key: str, default: int) -> int:
        try:
            value = int(get(key) or default)
        except ValueError:
            return default
        return value if value >= 0 else default

    limit = int_setting("TUTOR_LLM_DAILY_LIMIT", 40)
    global_limit = int_setting("TUTOR_LLM_GLOBAL_DAILY_LIMIT", 1000)

    return Config(
        token=token,
        owner_id=owner_id,
        anthropic_api_key=get("ANTHROPIC_API_KEY"),
        model=get("TUTOR_MODEL") or "claude-haiku-5-5",
        db_path=db_path,
        llm_daily_limit=limit,
        llm_global_daily_limit=global_limit,
        llm_marking=(get("TUTOR_LLM_MARKING") or "").strip().lower() in _TRUE,
    )
