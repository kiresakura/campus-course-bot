"""campus-course-bot entrypoint.

Selects which platform adapter to start based on the BOT_PLATFORM environment
variable (or --platform): discord (default) / telegram / line / cli.

Unofficial project, not affiliated with NCKUHUB or National Cheng Kung University.
"""

import argparse
import logging
import os
import sys

# Make sure the sibling core / adapters packages are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from core.course_service import CourseService
from core.demo import build_demo_service

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(PROJECT_ROOT, "data", "course_cache.json")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def build_adapter(platform: str, service: CourseService):
    """Build an adapter by platform name (SDKs are lazy-imported inside each adapter)."""
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
    if platform == "cli":
        from adapters.cli_adapter import CliAdapter

        return CliAdapter(service)
    raise RuntimeError(f"Unknown platform '{platform}' (available: discord / telegram / line / cli)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="campus-course-bot",
        description="Multi-platform course-review bot (unofficial; not affiliated with NCKUHUB / NCKU).",
    )
    parser.add_argument(
        "--platform",
        default=os.getenv("BOT_PLATFORM", "discord"),
        help="Platform to start: discord (default) / telegram / line / cli (terminal, no account needed)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use the bundled fictional sample courses instead of data/course_cache.json "
        "(course data never touches the network)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.demo:
        service = build_demo_service()
        logging.info("Demo mode: fictional sample courses (not real courses or people), served offline")
    else:
        service = CourseService(CACHE_FILE)
    if service.cache.is_empty:
        logging.warning("Course cache is empty; run: python build_cache.py (or try --demo)")

    try:
        adapter = build_adapter(args.platform, service)
        adapter.start()
    except (RuntimeError, ValueError) as exc:
        # Show a clean message to the operator; never dump a traceback
        print(f"[error] Failed to start {args.platform} adapter: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
