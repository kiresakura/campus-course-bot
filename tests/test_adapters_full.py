"""Telegram / LINE adapter 邏輯測試（不需 SDK、不需網路、不起 server）。"""

import asyncio
import base64
import hashlib
import hmac
import json

from adapters.line_adapter import LineAdapter
from adapters.telegram_adapter import TelegramAdapter
from core.models import BotResponse


# ----------------------------- Telegram -----------------------------------
def test_telegram_render_html_escapes():
    a = TelegramAdapter(service=None)
    out = a.render(BotResponse(title="A & B <x>", description="d"))
    assert "<b>A &amp; B &lt;x&gt;</b>" in out
    assert "<x>" not in out  # 角括號已被跳脫


def test_telegram_render_backtick_to_code():
    a = TelegramAdapter(service=None)
    r = BotResponse(title="t")
    r.add_field("甜度", "`8.0/10`")
    assert "<code>8.0/10</code>" in a.render(r)


def test_telegram_chunk_respects_limit():
    a = TelegramAdapter(service=None)
    text = "\n".join("x" * 100 for _ in range(60))  # ~6060 chars
    chunks = a._chunk(text, limit=4096)
    assert len(chunks) >= 2
    assert all(len(c) <= 4096 for c in chunks)


def test_telegram_dispatch_search(service):
    a = TelegramAdapter(service=service)
    resp = asyncio.run(a._dispatch("課程", "微積分"))
    assert any("微積分" in f.name for f in resp.fields)


def test_telegram_dispatch_compare_needs_two(service):
    a = TelegramAdapter(service=service)
    resp = asyncio.run(a._dispatch("比較", "微積分"))  # 只有一個參數
    assert resp.title == "用法"


# ------------------------------- LINE -------------------------------------
def test_line_signature_verify():
    secret = "testsecret"
    a = LineAdapter(service=None, channel_access_token="x", channel_secret=secret)
    body = b'{"events":[]}'
    good = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    assert a.verify_signature(body, good) is True
    assert a.verify_signature(body, "wrong-signature") is False
    assert a.verify_signature(body, "") is False


def test_line_webhook_routes_text(service):
    a = LineAdapter(service=service, channel_access_token="x", channel_secret="s")
    body = json.dumps(
        {"events": [{"type": "message", "replyToken": "RT", "message": {"type": "text", "text": "課程 微積分"}}]}
    ).encode()
    replies = asyncio.run(a.handle_webhook_body(body))
    assert len(replies) == 1
    token, text = replies[0]
    assert token == "RT"
    assert "微積分" in text


def test_line_webhook_ignores_non_text(service):
    a = LineAdapter(service=service, channel_access_token="x", channel_secret="s")
    body = json.dumps(
        {"events": [{"type": "message", "replyToken": "RT", "message": {"type": "sticker"}}]}
    ).encode()
    assert asyncio.run(a.handle_webhook_body(body)) == []


def test_line_parse_unknown_shows_help(service):
    a = LineAdapter(service=service, channel_access_token="x", channel_secret="s")
    out = asyncio.run(a.parse_and_reply("隨便打字"))
    assert "可用指令" in out


def test_line_build_app_routes(service):
    a = LineAdapter(service=service, channel_access_token="x", channel_secret="s")
    app = a._build_app()
    routes = {(r.method, r.resource.canonical) for r in app.router.routes()}
    assert ("GET", "/health") in routes
    assert ("POST", "/callback") in routes


def test_line_callback_end_to_end(service):
    """真正起一個 aiohttp 測試 server，打 /callback（含簽章驗證）。"""
    from aiohttp.test_utils import TestClient, TestServer

    sent = []

    async def fake_send(session, reply_token, text):
        sent.append((reply_token, text))

    async def run():
        a = LineAdapter(service=service, channel_access_token="x", channel_secret="s")
        a._send_reply = fake_send  # 攔截對外 LINE API 呼叫
        body = json.dumps(
            {"events": [{"type": "message", "replyToken": "RT", "message": {"type": "text", "text": "課程 微積分"}}]}
        ).encode()
        good = base64.b64encode(hmac.new(b"s", body, hashlib.sha256).digest()).decode()
        async with TestClient(TestServer(a._build_app())) as client:
            ok = await client.post("/callback", data=body, headers={"X-Line-Signature": good})
            assert ok.status == 200
            bad = await client.post("/callback", data=b"{}", headers={"X-Line-Signature": "nope"})
            assert bad.status == 403

    asyncio.run(run())
    assert sent and sent[0][0] == "RT" and "微積分" in sent[0][1]
