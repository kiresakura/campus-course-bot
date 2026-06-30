"""LINE adapter (full implementation, webhook mode).

LINE uses a webhook: it needs a public HTTPS endpoint to receive callbacks. This
implementation uses the project's existing aiohttp to run a tiny web server, so
**no line-bot-sdk is required**:
- POST /callback: verify X-Line-Signature (HMAC-SHA256 + base64), parse events,
  and reply via the Messaging API using the reply token.
- GET  /health: health check.

Deployment note: LINE requires the webhook to be HTTPS. Put it behind a reverse
proxy / platform (e.g. Railway) and set the public URL as the Webhook URL in the
LINE Developers Console (pointing at /callback). User-facing replies are in Chinese.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
from typing import List, Optional, Tuple

from core.course_service import CourseService
from core.models import BotResponse
from .base import BotAdapter

logger = logging.getLogger(__name__)

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_TEXT_LIMIT = 5000


class LineAdapter(BotAdapter):
    def __init__(
        self,
        service: Optional[CourseService],
        channel_access_token: Optional[str] = None,
        channel_secret: Optional[str] = None,
        host: str = "0.0.0.0",
        port: Optional[int] = None,
    ):
        super().__init__(service)
        self.channel_access_token = channel_access_token or os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.channel_secret = channel_secret or os.getenv("LINE_CHANNEL_SECRET")
        self.host = host
        self.port = int(port or os.getenv("PORT", "8000"))

    # -- render -----------------------------------------------------------
    def render(self, response: BotResponse) -> str:
        """Render as a LINE plain-text message (strip Markdown marks, clamp to the limit)."""
        text = response.to_markdown().replace("**", "").replace("`", "").replace("_", "")
        return text[:LINE_TEXT_LIMIT]

    # -- signature verification (stdlib, no SDK) --------------------------
    def verify_signature(self, body: bytes, signature: str) -> bool:
        if not self.channel_secret or not signature:
            return False
        mac = hmac.new(self.channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
        expected = base64.b64encode(mac).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    # -- command parsing --------------------------------------------------
    async def parse_and_reply(self, user_text: str) -> str:
        """Turn user input ("<command> <arg>") into reply text."""
        parts = user_text.strip().split(maxsplit=1)
        command = parts[0] if parts else ""
        arg = parts[1] if len(parts) > 1 else ""
        s = self.service
        simple = {
            "課程": lambda: s.search(arg),
            "教授": lambda: s.professor(arg),
            "甜課": lambda: s.top_sweet(arg or None),
            "涼課": lambda: s.top_cold(arg or None),
        }
        if command in simple:
            return self.render(simple[command]())
        if command == "比較":
            two = arg.split()
            if len(two) >= 2:
                return self.render(s.compare(two[0], two[1]))
            return "用法：比較 課程A 課程B"
        if command == "雷課":
            try:
                return self.render(s.worst(int(arg) if arg else 5))
            except ValueError:
                return self.render(s.worst(5))
        if command == "詳細":
            try:
                return self.render(await s.detail(int(arg)))
            except ValueError:
                return "用法：詳細 課程ID（數字）"
        return "可用指令：課程 / 教授 / 甜課 / 涼課 / 比較 / 雷課 / 詳細\n例如：課程 微積分"

    async def handle_webhook_body(self, body: bytes) -> List[Tuple[str, str]]:
        """Parse a signature-verified webhook body into a list of (reply_token, reply_text)."""
        try:
            payload = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            logger.warning("[LINE] could not parse webhook body")
            return []
        replies: List[Tuple[str, str]] = []
        for event in payload.get("events", []):
            if event.get("type") != "message":
                continue
            message = event.get("message", {})
            if message.get("type") != "text":
                continue
            reply_token = event.get("replyToken")
            if reply_token:
                replies.append((reply_token, await self.parse_and_reply(message.get("text", ""))))
        return replies

    async def _send_reply(self, session, reply_token: str, text: str) -> None:
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }
        payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}
        try:
            async with session.post(LINE_REPLY_URL, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    logger.warning("[LINE] reply failed status=%s", resp.status)
        except Exception:
            logger.exception("[LINE] reply send failed")

    # -- HTTP handlers ----------------------------------------------------
    async def _health(self, request):
        from aiohttp import web

        return web.Response(text="ok")

    async def _callback(self, request):
        from aiohttp import ClientSession, web

        signature = request.headers.get("X-Line-Signature", "")
        body = await request.read()
        if not self.verify_signature(body, signature):
            logger.warning("[LINE] signature verification failed; rejecting request")
            return web.Response(status=403, text="invalid signature")
        replies = await self.handle_webhook_body(body)
        if replies:
            async with ClientSession() as session:
                for reply_token, text in replies:
                    await self._send_reply(session, reply_token, text)
        return web.Response(text="ok")

    def _build_app(self):
        """Build the aiohttp webhook server (/callback, /health)."""
        from aiohttp import web

        app = web.Application()
        app.router.add_get("/health", self._health)
        app.router.add_post("/callback", self._callback)
        return app

    # -- start ------------------------------------------------------------
    def start(self) -> None:
        from aiohttp import web  # aiohttp is a core dependency

        if not (self.channel_access_token and self.channel_secret):
            raise RuntimeError(
                "Missing LINE_CHANNEL_ACCESS_TOKEN / LINE_CHANNEL_SECRET (set them in the environment or .env)"
            )
        app = self._build_app()
        logger.info(
            "[LINE] webhook listening on %s:%s (expose over HTTPS; point the Webhook URL at /callback)",
            self.host,
            self.port,
        )
        web.run_app(app, host=self.host, port=self.port)
