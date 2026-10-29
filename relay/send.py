"""Usage: send.py CHAT_ID TEXT [BUTTON|BUTTON;BUTTON...]  (';' separates rows, '|' buttons in a row; '-' removes the keyboard)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import load_token, call

chat, text = sys.argv[1], sys.argv[2]
params = {"chat_id": chat, "text": text}
if len(sys.argv) > 3 and sys.argv[3] == "-":
    params["reply_markup"] = json.dumps({"remove_keyboard": True})
elif len(sys.argv) > 3:
    rows = [[{"text": b} for b in row.split("|")] for row in sys.argv[3].split(";")]
    params["reply_markup"] = json.dumps({"keyboard": rows, "resize_keyboard": True})
call(load_token(), "sendMessage", **params)
print("sent")
