"""LINE adapter。

狀態：介面 + 渲染已實作的骨架。LINE 採 Webhook 模型（需要對外 HTTPS endpoint），
與 Discord/Telegram 的長連線不同，因此完整上線需搭配一個 web server（如 FastAPI/Flask）
接收 callback —— 這部分留作後續強化。start() 在 SDK/權杖缺失時給出清楚訊息。

render() 會把 BotResponse 轉成 LINE 的純文字訊息（可直接用於 reply）。
"""

import logging
import os
from typing import Optional

from core.course_service import CourseService
from core.models import BotResponse
from .base import BotAdapter

logger = logging.getLogger(__name__)


class LineAdapter(BotAdapter):
    def __init__(
        self,
        service: CourseService,
        channel_access_token: Optional[str] = None,
        channel_secret: Optional[str] = None,
    ):
        super().__init__(service)
        self.channel_access_token = channel_access_token or os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.channel_secret = channel_secret or os.getenv("LINE_CHANNEL_SECRET")

    def render(self, response: BotResponse) -> str:
        """LINE 以純文字訊息呈現（Markdown 記號去除以符合 LINE 顯示）。"""
        text = response.to_markdown()
        return text.replace("**", "").replace("`", "").replace("_", "")

    async def parse_and_reply(self, user_text: str) -> str:
        """給 webhook handler 呼叫：把使用者輸入轉成回覆文字。

        慣例：使用者輸入「<指令> <參數>」，例如「課程 微積分」「詳細 1234」。
        """
        parts = user_text.strip().split(maxsplit=1)
        command = parts[0] if parts else ""
        arg = parts[1] if len(parts) > 1 else ""
        s = self.service
        mapping = {
            "課程": lambda: s.search(arg),
            "教授": lambda: s.professor(arg),
            "甜課": lambda: s.top_sweet(arg or None),
            "涼課": lambda: s.top_cold(arg or None),
        }
        if command in mapping:
            return self.render(mapping[command]())
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
        return "可用指令：課程 / 教授 / 甜課 / 涼課 / 比較 / 雷課 / 詳細"

    def start(self) -> None:
        try:
            import linebot  # noqa: F401  # lazy
        except ImportError as exc:
            raise RuntimeError(
                "未安裝 LINE SDK，請執行：pip install line-bot-sdk==3.11.0"
            ) from exc
        if not (self.channel_access_token and self.channel_secret):
            raise RuntimeError(
                "缺少 LINE_CHANNEL_ACCESS_TOKEN / LINE_CHANNEL_SECRET（請設定環境變數或 .env）"
            )
        raise RuntimeError(
            "LINE adapter 需搭配對外 Webhook server 才能上線（callback endpoint）。"
            "請參考 README 的 LINE 章節串接；render() 與 parse_and_reply() 已可使用。"
        )
