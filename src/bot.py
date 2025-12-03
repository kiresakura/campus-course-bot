"""
NCKUHUB Discord Bot - 主程式
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
import sys
import logging
from dotenv import load_dotenv

# 確保可以找到同目錄的模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 載入環境變數（從專案根目錄）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# 專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 確保 logs 資料夾存在
os.makedirs(os.path.join(PROJECT_ROOT, 'logs'), exist_ok=True)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'bot.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NCKUHubBot(commands.Bot):
    """NCKUHUB 查詢機器人"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',  # 保留傳統指令前綴（備用）
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        """Bot 啟動時的初始化"""
        # 載入指令模組
        await self.load_extension('commands')
        logger.info("已載入課程查詢指令模組")

        # 載入李鴻章 RAG 指令模組
        try:
            await self.load_extension('rag_commands')
            logger.info("已載入李鴻章角色扮演模組")
        except Exception as e:
            logger.warning(f"李鴻章模組載入失敗: {e}")
        
        # 同步 Slash Commands
        guild_id = os.getenv('GUILD_ID')
        if guild_id:
            # 開發模式：只同步到測試伺服器（即時生效）
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"已同步指令到測試伺服器 {guild_id}")
        else:
            # 正式模式：全域同步（最多等1小時）
            await self.tree.sync()
            logger.info("已全域同步指令")
    
    async def on_ready(self):
        """Bot 上線時觸發"""
        logger.info(f'✅ 已登入: {self.user} (ID: {self.user.id})')
        logger.info(f'📊 伺服器數量: {len(self.guilds)}')
        
        # 設定狀態
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="NCKUHUB 課程評價 | /課程"
            )
        )
    
    async def on_error(self, event, *args, **kwargs):
        """錯誤處理"""
        logger.exception(f"事件 {event} 發生錯誤")


async def main():
    """主函式"""
    # 取得 Token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("❌ 找不到 DISCORD_TOKEN！請檢查 .env 檔案")
        return
    
    # 啟動 Bot
    bot = NCKUHubBot()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
