"""Long-polls the bot and prints one line per incoming message (for Claude to read)."""
import json, os, sys, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import load_token, call

token = load_token()
offset = 0
while True:
    try:
        updates = call(token, "getUpdates", offset=offset, timeout=30)
    except Exception as e:
        print(f"ERROR {e}", flush=True); time.sleep(5); continue
    for u in updates:
        offset = u["update_id"] + 1
        m = u.get("message") or {}
        if m:
            who = m["from"].get("username") or m["from"].get("first_name")
            text = m.get("text") or "[non-text message]"
            print(json.dumps({"bot": os.environ.get("BOT", "maths"), "chat": m["chat"]["id"], "from": who, "text": text}, ensure_ascii=False), flush=True)
