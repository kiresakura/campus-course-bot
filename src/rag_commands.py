"""
NCKUHUB Discord Bot - 李鴻章角色扮演指令
"""

import os
import re
import discord
from discord.ext import commands
from discord import app_commands

from rag.li_hongzhang import LiHongzhangRAG


class RAGCommands(commands.Cog):
    """李鴻章角色扮演指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 使用專案根目錄的 data 資料夾
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, 'data', 'lihongzhang')
        self.rag = LiHongzhangRAG(data_dir=data_dir)

    @app_commands.command(name="李鴻章", description="與晚清重臣李鴻章對話")
    @app_commands.describe(問題="你想問李鴻章什麼？")
    async def chat_with_li(self, interaction: discord.Interaction, 問題: str):
        """與李鴻章對話"""
        if not self.rag.is_available():
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⚠️ 服務不可用",
                    description="Claude API 尚未設定，無法進行對話。",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer()  # 可能需要時間處理

        response = await self.rag.chat(問題)

        embed = discord.Embed(
            title="🏛️ 李鴻章",
            description=response,
            color=0x8B4513  # 棕色，象徵歷史感
        )
        embed.set_footer(text="晚清重臣 • 洋務運動領袖 • 1823-1901")

        # 如果回應太長，分段顯示
        if len(response) > 4000:
            embed.description = response[:4000] + "..."

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="李鴻章簡介", description="查看李鴻章生平簡介")
    async def li_intro(self, interaction: discord.Interaction):
        """李鴻章簡介"""
        embed = discord.Embed(
            title="🏛️ 李鴻章（1823-1901）",
            description="晚清重臣、淮軍創始人、洋務運動領袖",
            color=0x8B4513
        )

        embed.add_field(
            name="📜 基本資料",
            value="字漸甫，號少荃\n安徽合肥人\n進士出身",
            inline=True
        )

        embed.add_field(
            name="🎖️ 主要官職",
            value="直隸總督（25年）\n北洋大臣\n文華殿大學士",
            inline=True
        )

        embed.add_field(
            name="⚔️ 軍事成就",
            value="• 創建淮軍\n• 建立北洋水師\n• 鎮壓太平天國",
            inline=False
        )

        embed.add_field(
            name="🏭 洋務事業",
            value="• 江南製造總局\n• 輪船招商局\n• 開平礦務局\n• 唐胥鐵路",
            inline=False
        )

        embed.add_field(
            name="📋 重大條約",
            value="• 《馬關條約》(1895)\n• 《辛丑條約》(1901)",
            inline=False
        )

        embed.add_field(
            name="💬 名言",
            value="「我辦了一輩子的事，練兵也，海軍也，都是紙糊的老虎。」",
            inline=False
        )

        embed.set_footer(text="使用 /李鴻章 <問題> 或 @李鴻章 與他對話")

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽訊息，當用戶 @ Bot 時觸發對話"""
        # 忽略 Bot 自己的訊息
        if message.author.bot:
            return

        # 檢查是否有 @ Bot
        if not self.bot.user.mentioned_in(message):
            return

        # 移除所有 @ 提及，取得實際問題內容
        # Discord mention 格式: <@123456> 或 <@!123456>
        content = re.sub(r'<@!?\d+>', '', message.content).strip()

        # 如果沒有內容，顯示簡介
        if not content:
            embed = discord.Embed(
                title="🏛️ 李鴻章",
                description="吾乃李鴻章，字漸甫，號少荃。有何事要問老夫？\n\n直接 @我 並提出你的問題即可。",
                color=0x8B4513
            )
            embed.set_footer(text="例如：@李鴻章 你對洋務運動有什麼看法？")
            await message.reply(embed=embed)
            return

        # 檢查 RAG 是否可用
        if not self.rag.is_available():
            embed = discord.Embed(
                title="⚠️ 服務不可用",
                description="Claude API 尚未設定，無法進行對話。",
                color=discord.Color.orange()
            )
            await message.reply(embed=embed)
            return

        # 顯示「正在輸入」狀態
        async with message.channel.typing():
            response = await self.rag.chat(content)

        embed = discord.Embed(
            title="🏛️ 李鴻章",
            description=response,
            color=0x8B4513
        )
        embed.set_footer(text="晚清重臣 • 洋務運動領袖 • 1823-1901")

        # 如果回應太長，截斷
        if len(response) > 4000:
            embed.description = response[:4000] + "..."

        await message.reply(embed=embed)


async def setup(bot: commands.Bot):
    """載入 Cog"""
    await bot.add_cog(RAGCommands(bot))
