"""
NCKUHUB Discord Bot - Slash Commands
"""

import os
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from nckuhub_api import NCKUHubAPI, Course
from embeds import CourseEmbeds


class CourseCommands(commands.Cog):
    """課程查詢相關指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 使用專案根目錄的 data 資料夾
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.api = NCKUHubAPI(cache_dir=os.path.join(project_root, 'data'))
        self.embeds = CourseEmbeds()
    
    @app_commands.command(name="課程", description="搜尋課程評價")
    @app_commands.describe(關鍵字="課程名稱、教授姓名或系所")
    async def search_course(self, interaction: discord.Interaction, 關鍵字: str):
        """搜尋課程"""
        await interaction.response.defer()  # 可能需要時間處理
        
        results = self.api.search_course(關鍵字)
        
        if not results:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🔍 找不到課程",
                    description=f"找不到符合「{關鍵字}」的課程\n試試其他關鍵字？",
                    color=discord.Color.orange()
                )
            )
            return
        
        embed = self.embeds.create_search_results(results, 關鍵字)
        await interaction.followup.send(embed=embed)

    
    @app_commands.command(name="教授", description="查詢教授的所有課程評價")
    @app_commands.describe(姓名="教授姓名")
    async def search_professor(self, interaction: discord.Interaction, 姓名: str):
        """查詢教授"""
        await interaction.response.defer()
        
        courses = self.api.get_professor_courses(姓名)
        
        if not courses:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="👨‍🏫 找不到教授",
                    description=f"找不到「{姓名}」老師的課程\n請確認姓名是否正確",
                    color=discord.Color.orange()
                )
            )
            return
        
        embed = self.embeds.create_professor_embed(姓名, courses)
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="甜課", description="推薦高甜度課程")
    @app_commands.describe(系所="可選：限定系所")
    async def sweet_courses(self, interaction: discord.Interaction, 系所: Optional[str] = None):
        """甜課推薦"""
        courses = self.api.get_top_sweet(limit=10, dept=系所)
        
        if not courses:
            await interaction.response.send_message("找不到符合條件的課程 😢")
            return
        
        embed = self.embeds.create_ranking_embed(
            courses, 
            title="🍬 甜度排行榜",
            sort_key='sweet'
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="涼課", description="推薦高涼度課程")
    @app_commands.describe(系所="可選：限定系所")
    async def cold_courses(self, interaction: discord.Interaction, 系所: Optional[str] = None):
        """涼課推薦"""
        courses = self.api.get_top_cold(limit=10, dept=系所)
        
        if not courses:
            await interaction.response.send_message("找不到符合條件的課程 😢")
            return
        
        embed = self.embeds.create_ranking_embed(
            courses,
            title="🛋️ 涼度排行榜", 
            sort_key='cold'
        )
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="比較", description="比較兩門課程")
    @app_commands.describe(課程a="第一門課程名稱", 課程b="第二門課程名稱")
    async def compare_courses(self, interaction: discord.Interaction, 課程a: str, 課程b: str):
        """課程 PK"""
        await interaction.response.defer()
        
        results_a = self.api.search_course(課程a, limit=1)
        results_b = self.api.search_course(課程b, limit=1)
        
        if not results_a or not results_b:
            missing = []
            if not results_a: missing.append(課程a)
            if not results_b: missing.append(課程b)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⚠️ 找不到課程",
                    description=f"找不到：{', '.join(missing)}",
                    color=discord.Color.orange()
                )
            )
            return
        
        embed = self.embeds.create_comparison_embed(results_a[0], results_b[0])
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="雷課", description="顯示低分課程警告")
    @app_commands.describe(數量="顯示幾門課程（預設5）")
    async def worst_courses(self, interaction: discord.Interaction, 數量: Optional[int] = 5):
        """雷課警報"""
        courses = self.api.get_worst_courses(limit=min(數量, 10))
        
        if not courses:
            await interaction.response.send_message("資料庫中沒有足夠的評分資料 🤔")
            return
        
        embed = self.embeds.create_ranking_embed(
            courses,
            title="⚠️ 雷課警報",
            sort_key='avg',
            ascending=True
        )
        embed.set_footer(text="⚠️ 僅供參考，每個人體驗可能不同")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="詳細", description="查看課程完整心得")
    @app_commands.describe(課程id="課程 ID（可從搜尋結果取得）")
    async def course_detail(self, interaction: discord.Interaction, 課程id: int):
        """課程詳細資訊"""
        await interaction.response.defer()
        
        course = await self.api.fetch_course(課程id)
        
        if not course:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ 找不到課程",
                    description=f"課程 ID {課程id} 不存在",
                    color=discord.Color.red()
                )
            )
            return
        
        embed = self.embeds.create_detail_embed(course)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """載入 Cog"""
    await bot.add_cog(CourseCommands(bot))
