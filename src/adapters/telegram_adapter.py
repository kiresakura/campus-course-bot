"""Telegram adapter。

狀態：可運作的骨架（render 已完整實作；start 會在 SDK/權杖缺失時給出
清楚的錯誤訊息，而非 traceback）。完整的指令互動細節可作為後續強化。

Telegram 的 bot 指令僅允許小寫英數與底線，因此中文指令以英文別名對應：
  /search /professor /sweet /cold /compare /worst /detail
"""

import logging
import os
from typing import Optional

from core.course_service import CourseService
from core.models import BotResponse
from .base import BotAdapter

logger = logging.getLogger(__name__)

# 中文指令 → 英文別名（Telegram 不支援非英數指令名）
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
    def __init__(self, service: CourseService, token: Optional[str] = None):
        super().__init__(service)
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")

    def render(self, response: BotResponse) -> str:
        """Telegram 以 Markdown 文字呈現。"""
        return response.to_markdown()

    def start(self) -> None:
        try:
            from telegram.ext import Application, CommandHandler  # lazy
        except ImportError as exc:
            raise RuntimeError(
                "未安裝 Telegram SDK，請執行：pip install python-telegram-bot==21.4"
            ) from exc
        if not self.token:
            raise RuntimeError("缺少 TELEGRAM_BOT_TOKEN（請設定環境變數或 .env）")

        app = Application.builder().token(self.token).build()

        def make_handler(zh_command: str):
            async def handler(update, context):
                arg = " ".join(context.args) if context.args else ""
                resp = await self._dispatch(zh_command, arg)
                await update.message.reply_markdown(self.render(resp))
            return handler

        for en_command, zh_command in COMMAND_ALIASES.items():
            app.add_handler(CommandHandler(en_command, make_handler(zh_command)))

        logger.info("Telegram adapter 啟動中…")
        app.run_polling()

    async def _dispatch(self, zh_command: str, arg: str) -> BotResponse:
        """把單一文字參數轉成對應的 service 呼叫。"""
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
