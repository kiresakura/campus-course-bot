"""Adapter abstract interface.

Adding a platform = subclass BotAdapter and implement render() and start().
Platform SDKs are always lazy-imported inside start() (or the constructor) so that
"importing this module" never hard-requires the corresponding SDK.
"""

from abc import ABC, abstractmethod
from typing import Any

from core.course_service import CourseService
from core.models import BotResponse

# Shared command set (Chinese command names). Each adapter maps user input to a
# service method itself.
COMMANDS = ("課程", "教授", "甜課", "涼課", "比較", "雷課", "詳細")


class BotAdapter(ABC):
    """Base class for all platform adapters."""

    def __init__(self, service: CourseService):
        self.service = service

    @abstractmethod
    def render(self, response: BotResponse) -> Any:
        """Turn a neutral BotResponse into the platform's message object."""
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """Connect and start serving (blocking; lazy-import the platform SDK here)."""
        raise NotImplementedError
