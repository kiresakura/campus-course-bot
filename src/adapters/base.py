"""Adapter 抽象介面。

新增一個平台 = 繼承 BotAdapter，實作 render() 與 start()。
平台 SDK 一律在 start()（或建構式）內 lazy import，
讓「import 這個模組」不會強制要求安裝對應 SDK。
"""

from abc import ABC, abstractmethod
from typing import Any

from core.course_service import CourseService
from core.models import BotResponse

# 平台共用的指令集合（中文指令名）。各 adapter 自行把使用者輸入對應到 service 方法。
COMMANDS = ("課程", "教授", "甜課", "涼課", "比較", "雷課", "詳細")


class BotAdapter(ABC):
    """所有平台 adapter 的基底。"""

    def __init__(self, service: CourseService):
        self.service = service

    @abstractmethod
    def render(self, response: BotResponse) -> Any:
        """把中性的 BotResponse 轉成該平台的訊息物件。"""
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """連線並開始服務（阻塞式；在此 lazy import 平台 SDK）。"""
        raise NotImplementedError
