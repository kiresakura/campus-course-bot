"""campus-course-bot 進入點。

依環境變數 BOT_PLATFORM（或 --platform）選擇要啟動的平台 adapter：
discord（預設）/ telegram / line。

非官方專案，與 NCKUHUB 及成功大學無任何隸屬關係。
"""

import argparse
import logging
import os
import sys

# 確保可以找到同目錄的 core / adapters 套件
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from core.course_service import CourseService

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(PROJECT_ROOT, "data", "course_cache.json")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def build_adapter(platform: str, service: CourseService):
    """依平台名稱建立 adapter（SDK 在各 adapter 內 lazy import）。"""
    platform = (platform or "discord").lower()
    if platform == "discord":
        from adapters.discord_adapter import DiscordAdapter

        return DiscordAdapter(
            service, token=os.getenv("DISCORD_TOKEN"), guild_id=os.getenv("GUILD_ID")
        )
    if platform == "telegram":
        from adapters.telegram_adapter import TelegramAdapter

        return TelegramAdapter(service)
    if platform == "line":
        from adapters.line_adapter import LineAdapter

        return LineAdapter(service)
    raise RuntimeError(f"未知平台「{platform}」（可用：discord / telegram / line）")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="campus-course-bot",
        description="多平台課程評價查詢機器人（非官方，與 NCKUHUB／成功大學無隸屬關係）。",
    )
    parser.add_argument(
        "--platform",
        default=os.getenv("BOT_PLATFORM", "discord"),
        help="要啟動的平台：discord（預設）/ telegram / line",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    service = CourseService(CACHE_FILE)
    if service.cache.is_empty:
        logging.warning("課程快取為空，請先執行：python build_cache.py")

    try:
        adapter = build_adapter(args.platform, service)
        adapter.start()
    except (RuntimeError, ValueError) as exc:
        # 對使用者顯示乾淨訊息，不噴 traceback
        print(f"❌ 無法啟動 {args.platform} adapter：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已停止。")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
