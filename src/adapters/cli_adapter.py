"""Terminal (CLI) adapter: chat with the bot in a terminal, no platform account needed.

Each input line is "<command> <args>". Commands are the Chinese names or their
English aliases, with or without a leading slash ("課程 微積分", "search dragon",
"/詳細 101"). Replies are the neutral Markdown text (BotResponse.to_markdown()).
"""

import asyncio

from core.models import BotResponse
from .base import COMMAND_ALIASES, BotAdapter

HELP_TEXT = """Commands (English alias or Chinese name):
  search <keyword>   課程  course name, instructor or department
  professor <name>   教授  average ratings across an instructor's courses
  sweet [dept]       甜課  sweetest courses (optionally within one department)
  cold [dept]        涼課  easiest courses
  compare <A> <B>    比較  head-to-head comparison
  worst [n]          雷課  lowest-rated courses (subjective, reference only)
  detail <id>        詳細  course card with comments
  help / quit"""


class CliAdapter(BotAdapter):
    def render(self, response: BotResponse) -> str:
        return response.to_markdown()

    async def reply(self, line: str) -> str:
        """Turn one input line into reply text (the help text if it is not a valid command)."""
        parts = line.strip().split(maxsplit=1)
        if not parts:
            return HELP_TEXT
        command = parts[0].lstrip("/")
        command = COMMAND_ALIASES.get(command.lower(), command)
        arg = parts[1] if len(parts) > 1 else ""
        s = self.service
        if command == "課程" and arg:
            return self.render(s.search(arg))
        if command == "教授" and arg:
            return self.render(s.professor(arg))
        if command == "甜課":
            return self.render(s.top_sweet(arg or None))
        if command == "涼課":
            return self.render(s.top_cold(arg or None))
        if command == "比較" and len(arg.split()) >= 2:
            a, b = arg.split()[:2]
            return self.render(s.compare(a, b))
        if command == "雷課":
            return self.render(s.worst(int(arg) if arg.isdecimal() else 5))
        if command == "詳細" and arg.isdecimal():
            return self.render(await s.detail(int(arg)))
        return HELP_TEXT

    def start(self) -> None:
        """Blocking read-eval-print loop on stdin/stdout; "quit" or EOF (Ctrl-D) exits."""
        print(HELP_TEXT)
        while True:
            try:
                line = input("\n> ")
            except EOFError:
                break
            if line.strip().lower() in ("quit", "exit"):
                break
            if line.strip():
                print(asyncio.run(self.reply(line)))
