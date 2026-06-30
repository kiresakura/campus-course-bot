"""Telegram adapter (full implementation, polling mode).

Telegram bot commands only allow lowercase letters/digits/underscore, so the
Chinese commands are exposed via English aliases:
  /search /professor /sweet /cold /compare /worst /detail
Replies use Telegram HTML parse mode and are chunked to fit the 4096-char limit.
The SDK is lazy-imported: importing this module does not require python-telegram-bot.
User-facing reply text is intentionally in Chinese.
"""

import html
import logging
import os
import re
from typing import Optional

from core.course_service import CourseService
from core.models import BotResponse
from .base import BotAdapter

logger = logging.getLogger(__name__)

TELEGRAM_MSG_LIMIT = 4096

# English alias → Chinese command (Telegram disallows non-alphanumeric command names)
COMMAND_ALIASES = {
    "search": "課程",
    "professor": "教授",
    "sweet": "甜課",
    "cold": "涼課",
    "compare": "比較",
    "worst": "雷課",
    "detail": "詳細",
}


class TelegramAdapter(BotAdapter):
    def __init__(self, service: Optional[CourseService], token: Optional[str] = None):
        super().__init__(service)
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")

    # -- render -----------------------------------------------------------
    def render(self, response: BotResponse) -> str:
        """BotResponse → Telegram HTML text."""
        def esc(s: object) -> str:
            return html.escape(str(s))

        parts = []
        if response.title:
            parts.append(f"<b>{esc(response.title)}</b>")
        if response.description:
            parts.append(esc(response.description))
        for f in response.fields:
            parts.append("")
            parts.append(f"<b>{esc(f.name)}</b>")
            if f.value:
                parts.append(esc(f.value))
        if response.footer:
            parts.append("")
            parts.append(f"<i>{esc(response.footer)}</i>")
        text = "\n".join(parts).strip()
        # `code` → <code>code</code> (backticks are not escaped by html.escape)
        return re.sub(r"`([^`]*)`", r"<code>\1</code>", text)

    @staticmethod
    def _chunk(text: str, limit: int = TELEGRAM_MSG_LIMIT):
        """Split on newlines so each chunk stays under Telegram's limit."""
        chunks, cur = [], ""
        for line in text.split("\n"):
            if len(cur) + len(line) + 1 > limit:
                if cur:
                    chunks.append(cur)
                cur = line[:limit]
            else:
                cur = f"{cur}\n{line}" if cur else line
        if cur:
            chunks.append(cur)
        return chunks or [""]

    def _help_text(self) -> str:
        lines = ["<b>📚 campus-course-bot</b>", "（非官方課程評價查詢）", "", "可用指令："]
        usage = {
            "search": "search 微積分",
            "professor": "professor 王小明",
            "sweet": "sweet [系所]",
            "cold": "cold [系所]",
            "compare": "compare 課程A 課程B",
            "worst": "worst [數量]",
            "detail": "detail 1234",
        }
        for en, zh in COMMAND_ALIASES.items():
            lines.append(f"/{html.escape(usage[en])} — {zh}")
        return "\n".join(lines)

    # -- command dispatch -------------------------------------------------
    async def _dispatch(self, zh_command: str, arg: str) -> BotResponse:
        s = self.service
        if zh_command == "課程":
            return s.search(arg)
        if zh_command == "教授":
            return s.professor(arg)
        if zh_command == "甜課":
            return s.top_sweet(arg or None)
        if zh_command == "涼課":
            return s.top_cold(arg or None)
        if zh_command == "比較":
            parts = arg.split()
            if len(parts) < 2:
                return BotResponse(title="用法", description="/compare 課程A 課程B")
            return s.compare(parts[0], parts[1])
        if zh_command == "雷課":
            try:
                limit = int(arg) if arg else 5
            except ValueError:
                limit = 5
            return s.worst(limit)
        if zh_command == "詳細":
            try:
                return await s.detail(int(arg))
            except ValueError:
                return BotResponse(title="用法", description="/detail 課程ID（數字）")
        return BotResponse(title="未知指令", description=zh_command)

    # -- start ------------------------------------------------------------
    def _build_app(self):
        """Build the Application and register all handlers (needs python-telegram-bot)."""
        from telegram.ext import Application, CommandHandler  # lazy

        app = Application.builder().token(self.token).build()

        async def help_handler(update, context):
            await update.message.reply_text(self._help_text(), parse_mode="HTML")

        def make_handler(zh_command: str):
            async def handler(update, context):
                arg = " ".join(context.args) if context.args else ""
                resp = await self._dispatch(zh_command, arg)
                for chunk in self._chunk(self.render(resp)):
                    await update.message.reply_text(chunk, parse_mode="HTML")
            return handler

        app.add_handler(CommandHandler("start", help_handler))
        app.add_handler(CommandHandler("help", help_handler))
        for en_command, zh_command in COMMAND_ALIASES.items():
            app.add_handler(CommandHandler(en_command, make_handler(zh_command)))
        return app

    def start(self) -> None:
        if not self.token:
            raise RuntimeError("Missing TELEGRAM_BOT_TOKEN (set it in the environment or .env)")
        try:
            app = self._build_app()
        except ImportError as exc:
            raise RuntimeError(
                "Telegram SDK not installed; run: pip install python-telegram-bot==21.4"
            ) from exc
        logger.info("Telegram adapter starting (polling)...")
        app.run_polling()
