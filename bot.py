"""Minimal Telegram bot: connects by token, verifies it and echoes messages.

Token is read from the TELEGRAM_BOT_TOKEN environment variable (or a .env file).
Uses only the Python standard library.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"


def load_token():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token and os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                key, _, value = line.strip().partition("=")
                if key == "TELEGRAM_BOT_TOKEN":
                    token = value.strip().strip('"').strip("'")
    if not token:
        sys.exit("Set TELEGRAM_BOT_TOKEN (env var or .env file)")
    return token


def call(token, method, timeout=35, **params):
    data = urllib.parse.urlencode(params).encode()
    url = API.format(token=token, method=method)
    try:
        with urllib.request.urlopen(url, data=data, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        payload = json.load(e)
    if not payload.get("ok"):
        raise RuntimeError(f"{method}: {payload.get('description')}")
    return payload["result"]


def main():
    token = load_token()
    me = call(token, "getMe")
    print(f"Connected as @{me['username']} (id {me['id']})")
    if "--check" in sys.argv:
        return

    offset = 0
    while True:
        try:
            updates = call(token, "getUpdates", offset=offset, timeout=30)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
            print(f"Error: {e}; retrying in 5s")
            time.sleep(5)
            continue
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message or "text" not in message:
                continue
            chat_id = message["chat"]["id"]
            text = message["text"]
            print(f"[{chat_id}] {text}")
            reply = "Бот подключён. Отправь мне любое сообщение." if text == "/start" else text
            call(token, "sendMessage", chat_id=chat_id, text=reply)


if __name__ == "__main__":
    main()
