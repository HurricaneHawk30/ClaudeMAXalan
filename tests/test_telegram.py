import http.client
import io
import json
import logging
import unittest
import urllib.error
from urllib.parse import parse_qs

import helpers
from helpers import make_engine
from tutor.db import Store
from tutor.messages import Incoming, Outgoing
from tutor.telegram import TelegramAPI, TelegramError, parse_update, run_polling, to_send_params


def upd(update_id, text="hi", chat=10, chat_type="private", key="message", **extra):
    msg = {"message_id": update_id, "chat": {"id": chat, "type": chat_type},
           "from": {"id": chat, "first_name": "Al", "username": "al"}, "date": 1}
    if text is not None:
        msg["text"] = text
    msg.update(extra)
    return {"update_id": update_id, key: msg}


class TestParseUpdate(unittest.TestCase):
    def test_text(self):
        self.assertEqual(parse_update(upd(1, "hello")),
                         Incoming(chat_id=10, user_id=10, text="hello", first_name="Al", username="al",
                                  chat_type="private"))

    def test_photo_has_no_text(self):
        m = parse_update(upd(1, None, photo=[{"file_id": "x"}]))
        self.assertIsNotNone(m)
        self.assertIsNone(m.text)
        self.assertEqual(m.chat_id, 10)

    def test_sticker_has_no_text(self):
        m = parse_update(upd(1, None, sticker={"file_id": "x"}))
        self.assertIsNone(m.text)

    def test_group_is_parsed_with_chat_type(self):
        m = parse_update(upd(1, "hi", chat=-500, chat_type="group"))
        self.assertEqual((m.chat_id, m.chat_type), (-500, "group"))
        m = parse_update(upd(1, "hi", chat=-500, chat_type="supergroup"))
        self.assertEqual(m.chat_type, "supergroup")

    def test_edited_message_is_none(self):
        self.assertIsNone(parse_update(upd(1, "hi", key="edited_message")))

    def test_other_update_kinds_are_none(self):
        self.assertIsNone(parse_update({"update_id": 5}))
        self.assertIsNone(parse_update({"update_id": 5, "callback_query": {"id": "1"}}))
        self.assertIsNone(parse_update({"update_id": 5, "channel_post": {"text": "x"}}))

    def test_missing_optional_names(self):
        u = upd(1, "hi")
        del u["message"]["from"]["username"]
        del u["message"]["from"]["first_name"]
        m = parse_update(u)
        self.assertEqual((m.first_name, m.username), ("", ""))


class TestToSendParams(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(to_send_params(Outgoing(7, "hi")), [{"chat_id": 7, "text": "hi"}])

    def test_keyboard(self):
        out = to_send_params(Outgoing(7, "hi", keyboard=(("A", "B"), ("C",))))
        self.assertEqual(len(out), 1)
        self.assertEqual(set(out[0]), {"chat_id", "text", "reply_markup"})
        self.assertIsInstance(out[0]["reply_markup"], str)
        self.assertEqual(json.loads(out[0]["reply_markup"]),
                         {"keyboard": [[{"text": "A"}, {"text": "B"}], [{"text": "C"}]],
                          "resize_keyboard": True, "is_persistent": True})

    def test_remove_keyboard(self):
        out = to_send_params(Outgoing(7, "hi", remove_keyboard=True))
        self.assertEqual(json.loads(out[0]["reply_markup"]), {"remove_keyboard": True})
        self.assertEqual(set(out[0]), {"chat_id", "text", "reply_markup"})

    def test_no_parse_mode_ever(self):
        for o in (Outgoing(1, "a *b* _c_"), Outgoing(1, "x", keyboard=(("A",),)), Outgoing(1, "y" * 9000)):
            for p in to_send_params(o):
                self.assertNotIn("parse_mode", p)

    def test_long_text_hard_split_markup_on_last_only(self):
        out = to_send_params(Outgoing(7, "x" * 9000, keyboard=(("A",),)))
        self.assertEqual([len(p["text"]) for p in out], [4000, 4000, 1000])
        self.assertEqual(["reply_markup" in p for p in out], [False, False, True])
        self.assertTrue(all(p["chat_id"] == 7 for p in out))
        self.assertEqual("".join(p["text"] for p in out), "x" * 9000)

    def test_exact_limit_boundaries(self):
        self.assertEqual(len(to_send_params(Outgoing(7, "x" * 4000))), 1)
        self.assertEqual([len(p["text"]) for p in to_send_params(Outgoing(7, "x" * 4001))], [4000, 1])

    def test_split_at_last_newline(self):
        text = "a" * 3000 + "\n" + "b" * 3000
        out = to_send_params(Outgoing(7, text, remove_keyboard=True))
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["text"].rstrip("\n"), "a" * 3000)
        self.assertEqual(out[1]["text"].lstrip("\n"), "b" * 3000)
        self.assertNotIn("reply_markup", out[0])
        self.assertEqual(json.loads(out[1]["reply_markup"]), {"remove_keyboard": True})
        for p in out:
            self.assertLessEqual(len(p["text"]), 4000)

    def test_no_chunk_is_empty_and_content_preserved(self):
        text = "\n".join(f"line {i}" for i in range(2000))
        out = to_send_params(Outgoing(7, text))
        self.assertGreater(len(out), 1)
        for p in out:
            self.assertTrue(p["text"].strip())
            self.assertLessEqual(len(p["text"]), 4000)
        self.assertEqual("".join(p["text"] for p in out).replace("\n", ""), text.replace("\n", ""))


class FakeResponse:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def read(self, *a):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestTelegramAPI(unittest.TestCase):
    def api(self, result):
        self.seen = []

        def opener(req, *a, **kw):
            self.seen.append(req)
            if isinstance(result, BaseException):
                raise result
            return FakeResponse(result)
        return TelegramAPI("123:ABC", timeout=5, opener=opener)

    def form(self, req):
        data = req.data if hasattr(req, "data") else None
        return {k: v[0] for k, v in parse_qs(data.decode()).items()}

    def test_call_posts_urlencoded_to_method_url(self):
        api = self.api({"ok": True, "result": {"id": 1}})
        self.assertEqual(api.call("sendMessage", chat_id=5, text="hi there"), {"id": 1})
        req = self.seen[0]
        self.assertEqual(req.full_url, "https://api.telegram.org/bot123:ABC/sendMessage")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(self.form(req), {"chat_id": "5", "text": "hi there"})

    def test_get_me(self):
        api = self.api({"ok": True, "result": {"id": 1, "username": "bot"}})
        self.assertEqual(api.get_me()["username"], "bot")
        self.assertTrue(self.seen[0].full_url.endswith("/getMe"))

    def test_get_updates(self):
        api = self.api({"ok": True, "result": [{"update_id": 9}]})
        self.assertEqual(api.get_updates(9, timeout=7), [{"update_id": 9}])
        req = self.seen[0]
        self.assertTrue(req.full_url.endswith("/getUpdates"))
        f = self.form(req)
        self.assertEqual(f["offset"], "9")
        self.assertEqual(f["timeout"], "7")
        self.assertEqual(json.loads(f["allowed_updates"]), ["message"])

    def test_send_message(self):
        api = self.api({"ok": True, "result": {}})
        self.assertIsNone(api.send_message({"chat_id": 5, "text": "yo", "reply_markup": "{}"}))
        self.assertTrue(self.seen[0].full_url.endswith("/sendMessage"))
        self.assertEqual(self.form(self.seen[0])["reply_markup"], "{}")

    def test_api_error_raises_telegram_error(self):
        api = self.api({"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked"})
        with self.assertRaises(TelegramError) as cm:
            api.call("sendMessage", chat_id=1, text="x")
        self.assertEqual(cm.exception.code, 403)
        self.assertIn("Forbidden", str(cm.exception))

    def test_http_error_with_json_body(self):
        body = json.dumps({"ok": False, "error_code": 429, "description": "Too Many Requests: retry after 3",
                           "parameters": {"retry_after": 3}}).encode()
        err = urllib.error.HTTPError("u", 429, "Too Many", {}, io.BytesIO(body))
        api = self.api(err)
        with self.assertRaises(TelegramError) as cm:
            api.call("sendMessage", chat_id=1, text="x")
        self.assertEqual(cm.exception.code, 429)
        self.assertEqual(cm.exception.retry_after, 3)

    def test_non_json_body(self):
        api = self.api(b"<html>bad gateway</html>")
        with self.assertRaises(TelegramError):
            api.call("getMe")

    def test_network_error_propagates_as_oserror(self):
        api = self.api(urllib.error.URLError("down"))
        with self.assertRaises(OSError):
            api.call("getMe")
        api = self.api(TimeoutError("slow"))
        with self.assertRaises(OSError):
            api.call("getMe")

    def test_telegram_error_attributes(self):
        e = TelegramError("desc", 429, 5)
        self.assertEqual((e.code, e.retry_after), (429, 5))
        self.assertIn("desc", str(e))
        e = TelegramError("plain")
        self.assertEqual((e.code, e.retry_after), (None, None))


# --------------------------------------------------------------------------- run_polling
class StopLoop(Exception):
    pass


class FakeAPI:
    """script: list of items per get_updates call; an Exception instance is raised, a list is returned."""

    def __init__(self, script, send_script=None):
        self.script = list(script)
        self.offsets = []
        self.sent = []
        self.send_attempts = 0
        self.send_script = list(send_script or [])
        self.stop = False

    def get_updates(self, offset, timeout=30):
        self.offsets.append(offset)
        if len(self.offsets) > 60:          # runaway loop guard (the loop itself never raises)
            self.stop = True
            return []
        if not self.script:
            self.stop = True
            return []
        item = self.script.pop(0)
        if not self.script:
            self.stop = True
        if isinstance(item, BaseException):
            raise item
        return item

    def send_message(self, params):
        self.send_attempts += 1
        if self.send_script:
            item = self.send_script.pop(0)
            if isinstance(item, BaseException):
                raise item
        self.sent.append(params)


class FakeEngine:
    def __init__(self, fail_on=()):
        self.handled = []
        self.fail_on = set(fail_on)
        self.undelivered = []

    def handle(self, msg):
        self.handled.append(msg)
        if msg.text in self.fail_on:
            raise RuntimeError("engine blew up")
        return [Outgoing(msg.chat_id, f"re: {msg.text}")]

    def on_delivery_failed(self, chat_id):
        self.undelivered.append(chat_id)


class FlakyStore:
    """A store whose set_offset fails for the first ``fails`` calls (e.g. 'database is locked')."""

    def __init__(self, real, fails):
        self.real, self.fails = real, fails

    def get_offset(self):
        return self.real.get_offset()

    def set_offset(self, offset):
        if self.fails:
            self.fails -= 1
            raise Exception("database is locked")
        self.real.set_offset(offset)


class TestRunPolling(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.sleeps = []

    def run_loop(self, api, engine=None, **kw):
        engine = engine or FakeEngine()
        run_polling(api, engine, self.store, sleep=self.sleeps.append, should_stop=lambda: api.stop, **kw)
        return engine

    def test_offset_read_once_and_saved(self):
        self.store.set_offset(10)
        api = FakeAPI([[upd(10, "a"), upd(11, "b")], [upd(12, "c")]])
        eng = self.run_loop(api)
        self.assertEqual(api.offsets[0], 10)
        self.assertEqual(api.offsets[1], 12)
        self.assertEqual(self.store.get_offset(), 13)
        self.assertEqual([m.text for m in eng.handled], ["a", "b", "c"])
        self.assertEqual([p["text"] for p in api.sent], ["re: a", "re: b", "re: c"])
        self.assertEqual([p["chat_id"] for p in api.sent], [10, 10, 10])

    def test_get_updates_failure_backs_off_and_continues(self):
        api = FakeAPI([OSError("net"), TimeoutError("t"), TelegramError("oops", 500), [upd(1, "ok")]])
        eng = self.run_loop(api)
        self.assertEqual(self.sleeps[:3], [1, 2, 4])
        self.assertEqual([m.text for m in eng.handled], ["ok"])

    def test_any_get_updates_exception_backs_off_and_continues(self):
        api = FakeAPI([http.client.IncompleteRead(b"partial"), http.client.RemoteDisconnected("bye"),
                       ValueError("bad json"), RuntimeError("weird"), [upd(1, "ok")]])
        eng = self.run_loop(api)
        self.assertEqual(self.sleeps[:4], [1, 2, 4, 8])
        self.assertEqual([m.text for m in eng.handled], ["ok"])
        self.assertEqual(self.store.get_offset(), 2)

    def test_incomplete_read_from_real_api_call(self):
        class Resp(FakeResponse):
            def read(self, *a):
                raise http.client.IncompleteRead(b"{")
        api = TelegramAPI("1:A", opener=lambda req, timeout=None: Resp(b""))
        with self.assertRaises(http.client.IncompleteRead):
            api.get_updates(0)

        class Wrapper:
            calls = 0

            def get_updates(self, offset, timeout=30):
                Wrapper.calls += 1
                if Wrapper.calls == 1:
                    return api.get_updates(offset, timeout)
                return [upd(1, "after")]

            def send_message(self, params):
                pass
        w = Wrapper()
        eng = FakeEngine()
        run_polling(w, eng, self.store, sleep=self.sleeps.append, should_stop=lambda: Wrapper.calls >= 2)
        self.assertEqual(self.sleeps[:1], [1])
        self.assertEqual([m.text for m in eng.handled], ["after"])

    def test_failing_set_offset_does_not_stop_the_loop(self):
        api = FakeAPI([[upd(1, "a")], [upd(2, "b")], [upd(3, "c")]])
        eng = FakeEngine()
        run_polling(api, eng, FlakyStore(self.store, 2), sleep=self.sleeps.append, should_stop=lambda: api.stop)
        self.assertEqual([m.text for m in eng.handled], ["a", "b", "c"])
        self.assertEqual(api.offsets, [0, 2, 3])        # the offset in memory advanced even when saving failed
        self.assertEqual(self.store.get_offset(), 4)

    def test_send_unexpected_exception_is_retried(self):
        api = FakeAPI([[upd(1, "a")]], send_script=[http.client.IncompleteRead(b"x")])
        self.run_loop(api)
        self.assertEqual(api.send_attempts, 2)
        self.assertEqual(len(api.sent), 1)

    def test_delivery_failure_is_reported_to_the_engine(self):
        api = FakeAPI([[upd(1, "a", chat=10), upd(2, "b", chat=11)]],
                      send_script=[TelegramError("Forbidden: bot was blocked by the user", 403)])
        eng = self.run_loop(api)
        self.assertEqual(eng.undelivered, [10])
        api = FakeAPI([[upd(3, "c", chat=12)]], send_script=[OSError("x")] * 3)
        eng = self.run_loop(api)
        self.assertEqual(eng.undelivered, [12])

    def test_engine_without_delivery_hook_is_fine(self):
        class Bare:
            def handle(self, msg):
                return [Outgoing(msg.chat_id, "x")]
        api = FakeAPI([[upd(1, "a")]], send_script=[TelegramError("Forbidden", 403)])
        self.run_loop(api, Bare())
        self.assertEqual(self.store.get_offset(), 2)

    def test_backoff_caps_at_60(self):
        api = FakeAPI([OSError("net")] * 10 + [[]])
        self.run_loop(api)
        self.assertEqual(self.sleeps[:10], [1, 2, 4, 8, 16, 32, 60, 60, 60, 60])

    def test_409_is_logged(self):
        api = FakeAPI([TelegramError("Conflict: terminated by other getUpdates request", 409), []])
        with self.assertLogs(level="WARNING") as cm:
            self.run_loop(api)
        self.assertIn("another getUpdates consumer is running", "\n".join(cm.output))
        self.assertEqual(self.sleeps[:1], [1])

    def test_send_403_is_not_retried_and_loop_continues(self):
        api = FakeAPI([[upd(1, "a"), upd(2, "b")]],
                      send_script=[TelegramError("Forbidden: bot was blocked by the user", 403)])
        eng = self.run_loop(api)
        self.assertEqual(api.send_attempts, 2)            # 1 failed (not retried) + 1 for the second update
        self.assertEqual([p["text"] for p in api.sent], ["re: b"])
        self.assertEqual(self.store.get_offset(), 3)
        self.assertEqual(len(eng.handled), 2)

    def test_send_400_is_not_retried(self):
        api = FakeAPI([[upd(1, "a")]], send_script=[TelegramError("Bad Request: chat not found", 400)])
        self.run_loop(api)
        self.assertEqual(api.send_attempts, 1)
        self.assertEqual(self.store.get_offset(), 2)

    def test_send_429_waits_retry_after_then_succeeds(self):
        api = FakeAPI([[upd(1, "a")]], send_script=[TelegramError("Too Many Requests", 429, retry_after=3)])
        self.run_loop(api)
        self.assertEqual(api.send_attempts, 2)
        self.assertIn(3, self.sleeps)
        self.assertEqual([p["text"] for p in api.sent], ["re: a"])

    def test_send_network_error_retries_up_to_three_times(self):
        api = FakeAPI([[upd(1, "a")]], send_script=[OSError("x"), OSError("y"), OSError("z"), OSError("never")])
        self.run_loop(api)
        self.assertEqual(api.send_attempts, 3)
        self.assertEqual(self.sleeps[:2], [1, 2])
        self.assertEqual(api.sent, [])
        self.assertEqual(self.store.get_offset(), 2)

    def test_send_network_error_then_success(self):
        api = FakeAPI([[upd(1, "a")]], send_script=[OSError("x")])
        self.run_loop(api)
        self.assertEqual(api.send_attempts, 2)
        self.assertEqual(self.sleeps[:1], [1])
        self.assertEqual(len(api.sent), 1)

    def test_engine_exception_still_advances_offset(self):
        api = FakeAPI([[upd(1, "boom"), upd(2, "fine")]])
        eng = self.run_loop(api, FakeEngine(fail_on={"boom"}))
        self.assertEqual(self.store.get_offset(), 3)
        self.assertEqual([m.text for m in eng.handled], ["boom", "fine"])
        self.assertEqual([p["text"] for p in api.sent], ["re: fine"])

    def test_unparseable_updates_are_skipped_but_acknowledged(self):
        api = FakeAPI([[upd(5, "edited", key="edited_message"), {"update_id": 6, "callback_query": {}}, upd(7, "real")]])
        eng = self.run_loop(api)
        self.assertEqual([m.text for m in eng.handled], ["real"])
        self.assertEqual(self.store.get_offset(), 8)

    def test_multiple_outgoing_are_all_sent_in_order(self):
        class Multi:
            def handle(self, msg):
                return [Outgoing(msg.chat_id, "one"), Outgoing(msg.chat_id, "two", keyboard=(("A",),))]
        api = FakeAPI([[upd(1, "x")]])
        self.run_loop(api, Multi())
        self.assertEqual([p["text"] for p in api.sent], ["one", "two"])
        self.assertIn("reply_markup", api.sent[1])

    def test_should_stop_true_immediately(self):
        api = FakeAPI([[upd(1, "x")]])
        run_polling(api, FakeEngine(), self.store, sleep=self.sleeps.append, should_stop=lambda: True)
        self.assertLessEqual(len(api.offsets), 1)

    def test_logs_never_contain_message_texts(self):
        secret = "SECRETTEXT-8841"
        root = logging.getLogger()
        old = root.level
        records = []

        class H(logging.Handler):
            def emit(self, rec):
                records.append(rec.getMessage())
        h = H(level=logging.DEBUG)
        root.addHandler(h)
        root.setLevel(logging.DEBUG)
        try:
            api = FakeAPI([[upd(1, secret), upd(2, secret + "x")]], send_script=[TelegramError("Forbidden", 403)])
            self.run_loop(api, FakeEngine(fail_on={secret + "x"}))
        finally:
            root.removeHandler(h)
            root.setLevel(old)
        self.assertFalse([r for r in records if secret in r], records)

    def test_undelivered_problem_is_not_marked(self):
        engine, store, clock = make_engine(flood=1000)
        self.addCleanup(store.close)
        helpers.to_topic(engine, 10)
        self.assertIsNotNone(store.get_pending(10))
        api = FakeAPI([[upd(1, "skip", chat=10)]], send_script=[OSError("down")] * 6)
        run_polling(api, engine, store, sleep=self.sleeps.append, should_stop=lambda: api.stop)
        self.assertIsNone(store.get_pending(10))         # the next problem never arrived: forget it
        out = helpers.send(engine, 10, "42")
        self.assertEqual(out[0].text, helpers.TOPIC_ASK(11))

    def test_on_delivery_failed_clears_only_that_chat(self):
        engine, store, clock = make_engine(flood=1000)
        self.addCleanup(store.close)
        helpers.to_topic(engine, 10)
        helpers.to_topic(engine, 11)
        engine.on_delivery_failed(10)
        self.assertIsNone(store.get_pending(10))
        self.assertIsNotNone(store.get_pending(11))
        engine.on_delivery_failed(12345)                 # unknown chat: no error

    def test_real_engine_end_to_end(self):
        engine, store, clock = make_engine(flood=1000)
        self.addCleanup(store.close)
        code = helpers.get_codes(engine, 1)[0]
        api = FakeAPI([[upd(1, "/start"), upd(2, code)]])
        run_polling(api, engine, self.store, sleep=self.sleeps.append, should_stop=lambda: api.stop)
        texts = [p["text"] for p in api.sent]
        self.assertEqual(texts[0], helpers.CODE_REQUEST)
        self.assertEqual(json.loads(api.sent[0]["reply_markup"]), {"remove_keyboard": True})
        self.assertEqual(texts[1], helpers.CODE_OK)
        self.assertEqual(texts[2], helpers.SUBJECT_ASK(11))
        self.assertEqual(json.loads(api.sent[2]["reply_markup"])["keyboard"],
                         [[{"text": "Maths"}, {"text": "Physics"}], [{"text": "🎓 Change year"}]])


if __name__ == "__main__":
    unittest.main()


class TestRunForever(unittest.TestCase):
    def test_restarts_after_unexpected_exception_with_backoff(self):
        from tutor.__main__ import run_forever
        calls, sleeps = [], []

        def run():
            calls.append(1)
            if len(calls) <= 3:
                raise RuntimeError("polling crashed")
        with self.assertLogs("tutor", level="ERROR"):
            run_forever(run, sleep=sleeps.append)
        self.assertEqual(len(calls), 4)
        self.assertEqual(sleeps, [1, 2, 4])

    def test_keyboard_interrupt_is_not_swallowed(self):
        from tutor.__main__ import run_forever

        def run():
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            run_forever(run, sleep=lambda s: None)

    def test_max_restarts(self):
        from tutor.__main__ import run_forever

        def run():
            raise ValueError("always")
        with self.assertLogs("tutor", level="ERROR"):
            with self.assertRaises(ValueError):
                run_forever(run, sleep=lambda s: None, max_restarts=2)

    def test_main_run_exits_0_on_ctrl_c(self):
        import tutor.__main__ as m
        import tutor.telegram as tg
        from unittest import mock

        def boom(*a, **kw):
            raise KeyboardInterrupt
        env = {"TELEGRAM_BOT_TOKEN": "1:A", "TUTOR_DB": ":memory:", "TUTOR_ENV_FILE": "/nonexistent/.env"}
        root = logging.getLogger()
        handlers, level = list(root.handlers), root.level
        try:
            with mock.patch.dict("os.environ", env), mock.patch.object(tg, "run_polling", boom):
                with self.assertLogs("tutor", level="INFO"):
                    self.assertEqual(m.main([]), 0)
        finally:                                   # main() calls logging.basicConfig: undo it
            for h in list(root.handlers):
                if h not in handlers:
                    root.removeHandler(h)
            root.setLevel(level)
