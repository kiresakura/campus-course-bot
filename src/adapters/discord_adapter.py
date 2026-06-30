"""Discord adapter（預設平台）。

discord SDK 採 lazy import：import 本模組不需要安裝 discord，
只有實際建立/啟動 adapter 時才需要。
"""

import logging
import os
from typing import Optional

from core.course_service import CourseService
from core.models import BotResponse, ResponseStyle
from .base import BotAdapter

logger = logging.getLogger(__name__)

# 語意化樣式 → Discord 顏色
_STYLE_COLORS = {
    ResponseStyle.PRIMARY: 0x5865F2,
    ResponseStyle.SUCCESS: 0x57F287,
    ResponseStyle.WARNING: 0xFEE75C,
    ResponseStyle.DANGER: 0xED4245,
    ResponseStyle.SWEET: 0xFF69B4,
    ResponseStyle.COLD: 0x87CEEB,
}


class DiscordAdapter(BotAdapter):
    def __init__(self, service: CourseService, token: str, guild_id: Optional[str] = None):
        super().__init__(service)
        if not token:
            raise ValueError("缺少 DISCORD_TOKEN")
        self.token = token
        self.guild_id = guild_id
        self._synced = False

        import discord  # lazy
        from discord.ext import commands as discord_commands

        intents = discord.Intents.default()  # 只用 slash command，不需 message_content
        self.bot = discord_commands.Bot(command_prefix="!", intents=intents, help_command=None)
        self._register()

    # -- 渲染 -------------------------------------------------------------
    def render(self, response: BotResponse):
        import discord  # lazy

        embed = discord.Embed(
            title=response.title or None,
            description=response.description or None,
            color=_STYLE_COLORS.get(response.style, 0x5865F2),
        )
        for f in response.fields:
            embed.add_field(name=f.name, value=f.value or "​", inline=f.inline)
        if response.footer:
            embed.set_footer(text=response.footer)
        return embed

    # -- 指令註冊 ---------------------------------------------------------
    def _register(self) -> None:
        import discord
        from discord import app_commands

        bot = self.bot
        service = self.service
        render = self.render

        @bot.tree.command(name="課程", description="搜尋課程評價")
        @app_commands.describe(關鍵字="課程名稱、教授姓名或系所")
        async def search(interaction: discord.Interaction, 關鍵字: str):
            await interaction.response.defer()
            await interaction.followup.send(embed=render(service.search(關鍵字)))

        @bot.tree.command(name="教授", description="查詢教授的所有課程評價")
        @app_commands.describe(姓名="教授姓名")
        async def professor(interaction: discord.Interaction, 姓名: str):
            await interaction.response.defer()
            await interaction.followup.send(embed=render(service.professor(姓名)))

        @bot.tree.command(name="甜課", description="推薦高甜度課程")
        @app_commands.describe(系所="可選：限定系所")
        async def sweet(interaction: discord.Interaction, 系所: Optional[str] = None):
            await interaction.response.send_message(embed=render(service.top_sweet(系所)))

        @bot.tree.command(name="涼課", description="推薦高涼度課程")
        @app_commands.describe(系所="可選：限定系所")
        async def cold(interaction: discord.Interaction, 系所: Optional[str] = None):
            await interaction.response.send_message(embed=render(service.top_cold(系所)))

        @bot.tree.command(name="比較", description="比較兩門課程")
        @app_commands.describe(課程a="第一門課程名稱", 課程b="第二門課程名稱")
        async def compare(interaction: discord.Interaction, 課程a: str, 課程b: str):
            await interaction.response.defer()
            await interaction.followup.send(embed=render(service.compare(課程a, 課程b)))

        @bot.tree.command(name="雷課", description="顯示低分課程警告")
        @app_commands.describe(數量="顯示幾門課程（預設 5）")
        async def worst(interaction: discord.Interaction, 數量: Optional[int] = 5):
            await interaction.response.send_message(embed=render(service.worst(數量 or 5)))

        @bot.tree.command(name="詳細", description="查看課程完整心得")
        @app_commands.describe(課程id="課程 ID（可從搜尋結果取得）")
        async def detail(interaction: discord.Interaction, 課程id: int):
            await interaction.response.defer()
            await interaction.followup.send(embed=render(await service.detail(課程id)))

        @bot.event
        async def on_ready():
            if not self._synced:
                guild_id = self.guild_id or os.getenv("GUILD_ID")
                if guild_id:
                    guild = discord.Object(id=int(guild_id))
                    bot.tree.copy_global_to(guild=guild)
                    await bot.tree.sync(guild=guild)
                    logger.info("已同步指令到測試伺服器 %s", guild_id)
                else:
                    await bot.tree.sync()
                    logger.info("已全域同步指令")
                self._synced = True
            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, name="課程評價 | /課程（非官方）"
                )
            )
            logger.info("✅ 已登入：%s", bot.user)

    def start(self) -> None:
        """阻塞式啟動（discord.py 自行管理事件迴圈）。"""
        self.bot.run(self.token)
