"""CLI: python3 -m tutor [--check] | codes N | sample SKILL_ID [LEVEL] [N]"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from .config import load_config, token_env_name

log = logging.getLogger("tutor")


def _int_range(lo: int, hi: int, name: str):
    def parse(value: str) -> int:
        try:
            n = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} must be an integer {lo}..{hi}") from None
        if not lo <= n <= hi:
            raise argparse.ArgumentTypeError(f"{name} must be in {lo}..{hi}")
        return n
    return parse


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python3 -m tutor", description="Telegram tutor engine")
    p.add_argument("--check", action="store_true", help="check the Telegram token and the LLM, then exit")
    sub = p.add_subparsers(dest="command")
    c = sub.add_parser("codes", help="generate N one-time access codes (prints codes only)")
    c.add_argument("n", type=_int_range(1, 1000, "N"))
    s = sub.add_parser("sample", help="print generated problems for a skill")
    s.add_argument("skill_id")
    s.add_argument("level", nargs="?", type=_int_range(1, 5, "LEVEL"), default=None)
    s.add_argument("n", nargs="?", type=_int_range(1, 50, "N"), default=3)
    return p


def _cmd_codes(n: int) -> int:
    from .db import Store
    config = load_config()
    store = Store(config.db_path)
    try:
        with store.transaction():
            codes = store.add_codes(n, time.time())
    finally:
        store.close()
    print("\n".join(codes))
    return 0


def _cmd_sample(skill_id: str, level: int | None, n: int) -> int:
    from .content import load_registry
    reg = load_registry()
    skill = reg.skill(skill_id)
    if skill is None:
        ids = sorted({s.id for subj in _all_subject_ids(reg) for s in reg.skills_of(subj)})
        print("Unknown skill. Available skill ids:\n" + "\n".join(ids), file=sys.stderr)
        return 2
    levels = [level] if level else [1, 2, 3, 4, 5]
    for lv in levels:
        for seed in range(1, n + 1):
            p = skill.generate(lv, seed)
            print(f"--- {skill_id} level {lv} seed {seed}")
            print(f"Q: {p.text}")
            print(f"A: {p.answer.display}")
            print(f"Solution: {p.solution}")
            print(f"Hint: {p.hint}")
    return 0


def _all_subject_ids(reg) -> list[str]:
    ids = []
    for year in reg.years():
        for subj in reg.subjects_for_year(year):
            if subj.id not in ids:
                ids.append(subj.id)
    return ids


def _make_llm(config):
    if not config.anthropic_api_key:
        return None
    from .llm import ClaudeLLM
    return ClaudeLLM(config.anthropic_api_key, config.model)


def _cmd_check() -> int:
    from .telegram import TelegramAPI, TelegramError
    config = load_config()
    if not config.token:
        print(f"Set {token_env_name()} (env var or .env file)", file=sys.stderr)
        return 1
    try:
        me = TelegramAPI(config.token).get_me()
    except (TelegramError, OSError) as e:
        print(f"Telegram check failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(f"Connected as @{me.get('username')} (id {me.get('id')})")
    llm = _make_llm(config)
    if llm is None:
        print("LLM: off (no ANTHROPIC_API_KEY)")
    elif llm.complete("Reply with one word.", "Say OK.", max_tokens=1) is not None:
        print(f"LLM: ok ({config.model})")
    else:
        print(f"LLM: FAILED ({config.model})")
    return 0


def _cmd_run() -> int:
    from .db import Store
    from .engine import Engine
    from .telegram import TelegramAPI, run_polling
    config = load_config()
    if not config.token:
        print(f"Set {token_env_name()} (env var or .env file)", file=sys.stderr)
        return 1
    llm = _make_llm(config)
    log.info("LLM: on (%s)" % config.model if llm else "LLM: off")
    if config.owner_id is None:
        log.warning("TUTOR_OWNER_ID is not set: owner commands and safety alerts are disabled")
    store = Store(config.db_path)
    try:
        engine = Engine(store, config, llm=llm)
        log.info("Polling started")
        run_polling(TelegramAPI(config.token), engine, store)
    except KeyboardInterrupt:
        log.info("Stopped")
    finally:
        store.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _build_parser().parse_args(argv)
    if args.command == "codes":
        return _cmd_codes(args.n)
    if args.command == "sample":
        return _cmd_sample(args.skill_id, args.level, args.n)
    if args.check:
        return _cmd_check()
    return _cmd_run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
