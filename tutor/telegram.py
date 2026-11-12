"""Minimal Telegram Bot API client and long-polling loop (standard library only)."""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

from .messages import Incoming, Outgoing

log = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}/{method}"
MAX_CHUNK = 4000


class TelegramError(Exception):
    def __init__(self, description: str, code: int | None = None, retry_after: int | None = None):
        super().__init__(description)
        self.description = description
        self.code = code
        self.retry_after = retry_after


class TelegramAPI:
    def __init__(self, token: str, timeout: int = 35, opener=urllib.request.urlopen):
        self._token = token
        self.timeout = timeout
        self._opener = opener

    def call(self, method: str, **params) -> object:
        encoded = {}
        for key, value in params.items():
            if isinstance(value, bool):
                encoded[key] = "true" if value else "false"
            elif isinstance(value, (list, dict)):
                encoded[key] = json.dumps(value)
            elif value is not None:
                encoded[key] = value
        data = urllib.parse.urlencode(encoded).encode()
        req = urllib.request.Request(API.format(token=self._token, method=method), data=data)
        status = None
        try:
            with self._opener(req, timeout=self.timeout) as resp:
                body = resp.read()
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                body = e.read()
            except Exception:
                body = b""
        try:
            payload = json.loads(body.decode("utf-8") if isinstance(body, bytes) else body)
        except (ValueError, UnicodeDecodeError):
            raise TelegramError("non-JSON response from Telegram", status) from None
        if not isinstance(payload, dict):
            raise TelegramError("unexpected response from Telegram", status)
        if not payload.get("ok"):
            params_ = payload.get("parameters") or {}
            raise TelegramError(str(payload.get("description")), payload.get("error_code", status),
                                params_.get("retry_after"))
        return payload.get("result")

    def get_me(self) -> dict:
        return self.call("getMe")  # type: ignore[return-value]

    def get_updates(self, offset: int, timeout: int = 30) -> list[dict]:
        return self.call("getUpdates", offset=offset, timeout=timeout,
                         allowed_updates=["message"])  # type: ignore[return-value]

    def send_message(self, params: dict) -> None:
        self.call("sendMessage", **params)


def parse_update(update: dict) -> Incoming | None:
    msg = update.get("message") if isinstance(update, dict) else None
    if not isinstance(msg, dict):
        return None
    chat = msg.get("chat") or {}
    sender = msg.get("from") or {}
    if "id" not in chat:
        return None
    text = msg.get("text")
    return Incoming(
        chat_id=chat["id"],
        user_id=sender.get("id", chat["id"]),
        text=text if isinstance(text, str) else None,
        first_name=sender.get("first_name", "") or "",
        username=sender.get("username", "") or "",
        chat_type=chat.get("type", "private"),
    )


def _chunks(text: str) -> list[str]:
    out = []
    while len(text) > MAX_CHUNK:
        cut = text.rfind("\n", 0, MAX_CHUNK)
        if cut <= 0:
            cut = MAX_CHUNK
        out.append(text[:cut])
        text = text[cut:].lstrip("\n") if cut != MAX_CHUNK else text[cut:]
    out.append(text)
    return out


def to_send_params(out: Outgoing) -> list[dict]:
    params = [{"chat_id": out.chat_id, "text": c} for c in _chunks(out.text)]
    if out.remove_keyboard:
        params[-1]["reply_markup"] = json.dumps({"remove_keyboard": True})
    elif out.keyboard:
        params[-1]["reply_markup"] = json.dumps({
            "keyboard": [[{"text": b} for b in row] for row in out.keyboard],
            "resize_keyboard": True,
            "is_persistent": True,
        })
    return params


def _send(api, params: dict, sleep: Callable[[float], None]) -> bool:
    for attempt in range(3):
        try:
            api.send_message(params)
            return True
        except TelegramError as e:
            if e.code in (400, 403):
                log.warning("send to chat %s rejected (%s)", params.get("chat_id"), e.code)
                return False
            if e.code == 429:
                sleep(e.retry_after or 1)
            else:
                sleep(2 ** attempt)
        except Exception as e:  # network errors, http.client.HTTPException / IncompleteRead, ...
            log.warning("send to chat %s failed: %s", params.get("chat_id"), type(e).__name__)
            sleep(2 ** attempt)
    log.warning("send to chat %s failed after 3 tries", params.get("chat_id"))
    return False


def _deliver(api, engine, outgoing: list[Outgoing], sleep: Callable[[float], None]) -> None:
    """Send every message in order; tell the engine about chats that could not be reached."""
    failed: list[int] = []
    for out in outgoing:
        if out.chat_id in failed:
            continue
        for params in to_send_params(out):
            if not _send(api, params, sleep):
                failed.append(out.chat_id)
                break
    notify = getattr(engine, "on_delivery_failed", None)
    for chat_id in failed:
        if notify is not None:
            notify(chat_id)


def run_polling(api, engine, store, *, sleep: Callable[[float], None] = time.sleep,
                should_stop: Callable[[], bool] = lambda: False) -> None:
    """Long-polling loop. It never raises: every failure is logged (type only) and retried."""
    try:
        offset = store.get_offset()
    except Exception as e:
        log.error("could not read the stored offset (%s); starting from 0", type(e).__name__)
        offset = 0
    backoff = 1
    while not should_stop():
        try:
            updates = api.get_updates(offset, 30)
            if not isinstance(updates, list):
                raise TelegramError("unexpected getUpdates result")
        except Exception as e:  # OSError, TelegramError, http.client.HTTPException, IncompleteRead, ...
            if isinstance(e, TelegramError) and e.code == 409:
                log.error("another getUpdates consumer is running for this token (409)")
            else:
                log.warning("getUpdates failed: %s; retrying in %ss", type(e).__name__, backoff)
            sleep(backoff)
            backoff = min(60, backoff * 2)
            continue
        backoff = 1
        for update in updates:
            update_id = update.get("update_id") if isinstance(update, dict) else None
            try:
                incoming = parse_update(update)
                if incoming is not None:
                    log.info("message from chat %s", incoming.chat_id)
                    _deliver(api, engine, engine.handle(incoming), sleep)
            except Exception as e:
                log.error("failed to process update %s: %s", update_id, type(e).__name__)
                sleep(1)
            if isinstance(update_id, int):
                offset = update_id + 1
                try:
                    store.set_offset(offset)
                except Exception as e:  # e.g. database locked: the offset in memory still advances
                    log.error("could not save offset %s: %s", offset, type(e).__name__)
                    sleep(1)
