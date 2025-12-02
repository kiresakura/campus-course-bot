"""
NCKUHUB Discord Bot - Embed 美化模組
"""

import discord
from typing import List, Dict


class CourseEmbeds:
    """Discord Embed 生成器"""
    
    # 顏色主題
    COLORS = {
        'primary': 0x5865F2,    # Discord 藍
        'success': 0x57F287,    # 綠色
        'warning': 0xFEE75C,    # 黃色
        'danger': 0xED4245,     # 紅色
        'sweet': 0xFF69B4,      # 粉紅（甜）
        'cold': 0x87CEEB,       # 天藍（涼）
    }
    
    def _score_bar(self, score: float, max_score: float = 10) -> str:
        """生成分數進度條"""
        filled = int((score / max_score) * 10)
        empty = 10 - filled
        return '█' * filled + '░' * empty
    
    def _score_emoji(self, score: float) -> str:
        """根據分數返回對應 emoji"""
        if score >= 8: return '🔥'
        if score >= 6: return '✨'
        if score >= 4: return '😐'
        return '💀'
    
    def create_course_embed(self, course: dict) -> discord.Embed:
        """建立單一課程的 Embed"""
        sweet = course.get('sweet', 0)
        cold = course.get('cold', 0)
        got = course.get('got', 0)
        
        embed = discord.Embed(
            title=f"📚 {course.get('name', '未知課程')}",
            description=f"**{course.get('dept', '')}** ｜ {course.get('teacher', '未知')}",
            color=self.COLORS['primary']
        )

        
        # 評分區塊
        embed.add_field(
            name="🍬 甜度",
            value=f"`{sweet:.1f}/10` {self._score_bar(sweet)} {self._score_emoji(sweet)}",
            inline=True
        )
        embed.add_field(
            name="🛋️ 涼度",
            value=f"`{cold:.1f}/10` {self._score_bar(cold)} {self._score_emoji(cold)}",
            inline=True
        )
        embed.add_field(
            name="📖 收穫",
            value=f"`{got:.1f}/10` {self._score_bar(got)} {self._score_emoji(got)}",
            inline=True
        )
        
        embed.add_field(
            name="👥 評分人數",
            value=str(course.get('rate_count', 0)),
            inline=True
        )
        
        embed.set_footer(text=f"課程 ID: {course.get('id', 'N/A')}")
        return embed
    
    def create_search_results(self, courses: List[dict], keyword: str) -> discord.Embed:
        """建立搜尋結果 Embed"""
        embed = discord.Embed(
            title=f"🔍 搜尋結果：{keyword}",
            description=f"找到 {len(courses)} 門課程",
            color=self.COLORS['primary']
        )
        
        for i, course in enumerate(courses[:10], 1):
            sweet = course.get('sweet', 0)
            cold = course.get('cold', 0)
            got = course.get('got', 0)
            
            embed.add_field(
                name=f"{i}. {course.get('name', '?')}",
                value=(
                    f"👨‍🏫 {course.get('teacher', '?')} ｜ {course.get('dept', '?')}\n"
                    f"🍬 `{sweet:.1f}` 🛋️ `{cold:.1f}` 📖 `{got:.1f}` ｜ 👥 {course.get('rate_count', 0)}\n"
                    f"📋 `/詳細 {course.get('id')}`"
                ),
                inline=False
            )
        
        return embed

    
    def create_professor_embed(self, name: str, courses: List[dict]) -> discord.Embed:
        """建立教授資訊 Embed"""
        # 計算平均分數
        if courses:
            avg_sweet = sum(c.get('sweet', 0) for c in courses) / len(courses)
            avg_cold = sum(c.get('cold', 0) for c in courses) / len(courses)
            avg_got = sum(c.get('got', 0) for c in courses) / len(courses)
        else:
            avg_sweet = avg_cold = avg_got = 0
        
        embed = discord.Embed(
            title=f"👨‍🏫 {name} 老師",
            description=f"共有 {len(courses)} 門課程",
            color=self.COLORS['primary']
        )
        
        # 平均評分
        embed.add_field(
            name="📊 平均評分",
            value=f"🍬 `{avg_sweet:.1f}` ｜ 🛋️ `{avg_cold:.1f}` ｜ 📖 `{avg_got:.1f}`",
            inline=False
        )
        
        # 課程列表
        for course in courses[:5]:
            embed.add_field(
                name=course.get('name', '?'),
                value=f"🍬 `{course.get('sweet', 0):.1f}` 🛋️ `{course.get('cold', 0):.1f}` 📖 `{course.get('got', 0):.1f}`",
                inline=True
            )
        
        if len(courses) > 5:
            embed.set_footer(text=f"還有 {len(courses) - 5} 門課程未顯示")
        
        return embed
    
    def create_ranking_embed(self, courses: List[dict], title: str, 
                            sort_key: str = 'sweet', ascending: bool = False) -> discord.Embed:
        """建立排行榜 Embed"""
        color = self.COLORS.get(sort_key, self.COLORS['primary'])
        
        embed = discord.Embed(title=title, color=color)
        
        medals = ['🥇', '🥈', '🥉'] + ['　'] * 7
        
        for i, course in enumerate(courses[:10]):
            score = course.get(sort_key, 0)
            if sort_key == 'avg':
                score = (course.get('sweet', 0) + course.get('cold', 0) + course.get('got', 0)) / 3
            
            embed.add_field(
                name=f"{medals[i]} {course.get('name', '?')}",
                value=f"👨‍🏫 {course.get('teacher', '?')}\n評分: `{score:.1f}` ｜ 👥 {course.get('rate_count', 0)}",
                inline=False
            )
        
        return embed

    
    def create_comparison_embed(self, course_a: dict, course_b: dict) -> discord.Embed:
        """建立課程比較 Embed"""
        embed = discord.Embed(
            title="⚔️ 課程 PK",
            color=self.COLORS['primary']
        )
        
        # 比較項目
        comparisons = [
            ('🍬 甜度', 'sweet'),
            ('🛋️ 涼度', 'cold'),
            ('📖 收穫', 'got'),
        ]
        
        a_wins = 0
        b_wins = 0
        
        embed.add_field(name="📚 課程", value=f"**{course_a.get('name')}**\nvs\n**{course_b.get('name')}**", inline=False)
        
        for label, key in comparisons:
            val_a = course_a.get(key, 0)
            val_b = course_b.get(key, 0)
            
            if val_a > val_b:
                winner = "⬅️"
                a_wins += 1
            elif val_b > val_a:
                winner = "➡️"
                b_wins += 1
            else:
                winner = "🤝"
            
            embed.add_field(
                name=label,
                value=f"`{val_a:.1f}` {winner} `{val_b:.1f}`",
                inline=True
            )
        
        # 勝負結果
        if a_wins > b_wins:
            result = f"🏆 **{course_a.get('name')}** 勝出！"
        elif b_wins > a_wins:
            result = f"🏆 **{course_b.get('name')}** 勝出！"
        else:
            result = "🤝 平手！"
        
        embed.add_field(name="📊 結果", value=result, inline=False)
        return embed
    
    def create_detail_embed(self, course) -> discord.Embed:
        """建立課程詳細資訊 Embed（含心得）"""
        embed = self.create_course_embed({
            'id': course.id,
            'name': course.name,
            'dept': course.dept,
            'teacher': course.teacher,
            'sweet': course.sweet,
            'cold': course.cold,
            'got': course.got,
            'rate_count': course.rate_count
        })
        
        # 加入心得
        if course.comments:
            for i, comment in enumerate(course.comments[:3], 1):
                text = comment.get('comment', '')[:200]
                if len(comment.get('comment', '')) > 200:
                    text += '...'
                semester = comment.get('semester', '?')
                
                embed.add_field(
                    name=f"💬 心得 #{i} ({semester})",
                    value=text or "（無內容）",
                    inline=False
                )
        else:
            embed.add_field(name="💬 心得", value="目前沒有心得", inline=False)
        
        return embed
