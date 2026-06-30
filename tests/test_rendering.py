"""Response rendering tests: neutral Markdown (platform-agnostic) + Discord Embed
(when discord is installed). Sample text is Chinese to mirror the production UI."""

import pytest

from core.models import BotResponse, ResponseStyle


def _sample() -> BotResponse:
    resp = BotResponse(title="📚 測試課程", description="數學系 ｜ 王小明", footer="課程 ID: 1")
    resp.add_field("🍬 甜度", "`8.0/10`", inline=True)
    resp.add_field("👥 評分人數", "10", inline=True)
    return resp


def test_to_markdown_contains_content():
    md = _sample().to_markdown()
    assert "測試課程" in md
    assert "甜度" in md
    assert "課程 ID: 1" in md


def test_telegram_render_is_text():
    from adapters.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter(service=None)  # render does not need a service
    out = adapter.render(_sample())
    assert isinstance(out, str)
    assert "測試課程" in out


def test_line_render_strips_markup():
    from adapters.line_adapter import LineAdapter

    adapter = LineAdapter(service=None)
    out = adapter.render(_sample())
    assert "**" not in out and "`" not in out
    assert "測試課程" in out


def test_discord_render_to_embed():
    discord = pytest.importorskip("discord")
    from adapters.discord_adapter import DiscordAdapter

    # construct with a fake token (offline; never connects)
    adapter = DiscordAdapter(service=None, token="dummy-token")
    embed = adapter.render(_sample())
    assert isinstance(embed, discord.Embed)
    assert embed.title == "📚 測試課程"
    assert len(embed.fields) == 2
