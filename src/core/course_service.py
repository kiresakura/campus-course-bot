"""課程查詢服務（平台無關）。

每個方法回傳一個 BotResponse，由各 adapter 渲染。此層不得 import 任何平台 SDK。
"""

import logging
from typing import List, Optional

from .cache import CourseCache
from .models import BotResponse, ResponseStyle
from .nckuhub_client import NCKUHubClient

logger = logging.getLogger(__name__)


def _score_bar(score: float, max_score: float = 10) -> str:
    filled = max(0, min(10, int((score / max_score) * 10)))
    return "█" * filled + "░" * (10 - filled)


def _score_emoji(score: float) -> str:
    if score >= 8:
        return "🔥"
    if score >= 6:
        return "✨"
    if score >= 4:
        return "😐"
    return "💀"


class CourseService:
    """課程查詢核心邏輯。"""

    def __init__(self, cache_file: str):
        self.cache = CourseCache(cache_file)
        self.client = NCKUHubClient(self.cache)

    # -- 內部小工具 -------------------------------------------------------
    def _course_card(self, course: dict, style: ResponseStyle = ResponseStyle.PRIMARY) -> BotResponse:
        sweet = course.get("sweet", 0)
        cold = course.get("cold", 0)
        got = course.get("got", 0)
        resp = BotResponse(
            title=f"📚 {course.get('name', '未知課程')}",
            description=f"**{course.get('dept', '')}** ｜ {course.get('teacher', '未知')}",
            footer=f"課程 ID: {course.get('id', 'N/A')}",
            style=style,
        )
        resp.add_field("🍬 甜度", f"`{sweet:.1f}/10` {_score_bar(sweet)} {_score_emoji(sweet)}", inline=True)
        resp.add_field("🛋️ 涼度", f"`{cold:.1f}/10` {_score_bar(cold)} {_score_emoji(cold)}", inline=True)
        resp.add_field("📖 收穫", f"`{got:.1f}/10` {_score_bar(got)} {_score_emoji(got)}", inline=True)
        resp.add_field("👥 評分人數", str(course.get("rate_count", 0)), inline=True)
        return resp

    @staticmethod
    def _not_found(title: str, desc: str) -> BotResponse:
        return BotResponse(title=title, description=desc, style=ResponseStyle.WARNING)

    # -- 指令 -------------------------------------------------------------
    def search(self, keyword: str) -> BotResponse:
        results = self.cache.search_course(keyword)
        if not results:
            return self._not_found("🔍 找不到課程", f"找不到符合「{keyword}」的課程，試試其他關鍵字？")
        resp = BotResponse(title=f"🔍 搜尋結果：{keyword}", description=f"找到 {len(results)} 門課程")
        for i, c in enumerate(results[:10], 1):
            resp.add_field(
                f"{i}. {c.get('name', '?')}",
                f"👨‍🏫 {c.get('teacher', '?')} ｜ {c.get('dept', '?')}\n"
                f"🍬 `{c.get('sweet', 0):.1f}` 🛋️ `{c.get('cold', 0):.1f}` 📖 `{c.get('got', 0):.1f}` ｜ 👥 {c.get('rate_count', 0)}\n"
                f"📋 `/詳細 {c.get('id')}`",
            )
        return resp

    def professor(self, name: str) -> BotResponse:
        courses = self.cache.get_professor_courses(name)
        if not courses:
            return self._not_found("👨‍🏫 找不到教授", f"找不到「{name}」老師的課程，請確認姓名是否正確。")
        avg_sweet = sum(c.get("sweet", 0) for c in courses) / len(courses)
        avg_cold = sum(c.get("cold", 0) for c in courses) / len(courses)
        avg_got = sum(c.get("got", 0) for c in courses) / len(courses)
        resp = BotResponse(title=f"👨‍🏫 {name} 老師", description=f"共有 {len(courses)} 門課程")
        resp.add_field("📊 平均評分", f"🍬 `{avg_sweet:.1f}` ｜ 🛋️ `{avg_cold:.1f}` ｜ 📖 `{avg_got:.1f}`")
        for c in courses[:5]:
            resp.add_field(
                c.get("name", "?"),
                f"🍬 `{c.get('sweet', 0):.1f}` 🛋️ `{c.get('cold', 0):.1f}` 📖 `{c.get('got', 0):.1f}`",
                inline=True,
            )
        if len(courses) > 5:
            resp.footer = f"還有 {len(courses) - 5} 門課程未顯示"
        return resp

    def top_sweet(self, dept: Optional[str] = None) -> BotResponse:
        courses = self.cache.get_top_sweet(limit=10, dept=dept)
        if not courses:
            return self._not_found("🍬 甜度排行榜", "找不到符合條件的課程 😢")
        return self._ranking(courses, "🍬 甜度排行榜", "sweet", ResponseStyle.SWEET)

    def top_cold(self, dept: Optional[str] = None) -> BotResponse:
        courses = self.cache.get_top_cold(limit=10, dept=dept)
        if not courses:
            return self._not_found("🛋️ 涼度排行榜", "找不到符合條件的課程 😢")
        return self._ranking(courses, "🛋️ 涼度排行榜", "cold", ResponseStyle.COLD)

    def worst(self, limit: int = 5) -> BotResponse:
        courses = self.cache.get_worst_courses(limit=max(1, min(limit, 10)))
        if not courses:
            return self._not_found("⚠️ 雷課警報", "資料庫中沒有足夠的評分資料 🤔")
        resp = self._ranking(courses, "⚠️ 雷課警報", "avg", ResponseStyle.DANGER, ascending=True)
        resp.footer = "⚠️ 主觀評價，僅供參考，每個人體驗可能不同"
        return resp

    def _ranking(
        self, courses: List[dict], title: str, sort_key: str, style: ResponseStyle, ascending: bool = False
    ) -> BotResponse:
        resp = BotResponse(title=title, style=style)
        medals = ["🥇", "🥈", "🥉"] + ["　"] * 7
        for i, c in enumerate(courses[:10]):
            if sort_key == "avg":
                score = (c.get("sweet", 0) + c.get("cold", 0) + c.get("got", 0)) / 3
            else:
                score = c.get(sort_key, 0)
            resp.add_field(
                f"{medals[i]} {c.get('name', '?')}",
                f"👨‍🏫 {c.get('teacher', '?')}\n評分: `{score:.1f}` ｜ 👥 {c.get('rate_count', 0)}",
            )
        return resp

    def compare(self, name_a: str, name_b: str) -> BotResponse:
        a = self.cache.search_course(name_a, limit=1)
        b = self.cache.search_course(name_b, limit=1)
        if not a or not b:
            missing = [n for n, r in ((name_a, a), (name_b, b)) if not r]
            return self._not_found("⚠️ 找不到課程", f"找不到：{', '.join(missing)}")
        ca, cb = a[0], b[0]
        resp = BotResponse(title="⚔️ 課程 PK")
        resp.add_field("📚 課程", f"**{ca.get('name')}**\nvs\n**{cb.get('name')}**")
        a_wins = b_wins = 0
        for label, key in (("🍬 甜度", "sweet"), ("🛋️ 涼度", "cold"), ("📖 收穫", "got")):
            va, vb = ca.get(key, 0), cb.get(key, 0)
            if va > vb:
                arrow, a_wins = "⬅️", a_wins + 1
            elif vb > va:
                arrow, b_wins = "➡️", b_wins + 1
            else:
                arrow = "🤝"
            resp.add_field(label, f"`{va:.1f}` {arrow} `{vb:.1f}`", inline=True)
        if a_wins > b_wins:
            result = f"🏆 **{ca.get('name')}** 勝出！"
        elif b_wins > a_wins:
            result = f"🏆 **{cb.get('name')}** 勝出！"
        else:
            result = "🤝 平手！"
        resp.add_field("📊 結果", result)
        return resp

    async def detail(self, course_id: int) -> BotResponse:
        """即時抓取課程完整資訊（含心得）。"""
        try:
            course = await self.client.fetch_course(course_id)
        except Exception:
            logger.exception("[detail] 抓取課程 %s 失敗", course_id)
            return self._not_found("⚠️ 暫時無法查詢", "查詢課程時發生問題，請稍後再試。")
        if not course:
            return BotResponse(
                title="❌ 找不到課程",
                description=f"課程 ID {course_id} 不存在",
                style=ResponseStyle.DANGER,
            )
        resp = self._course_card(course.to_dict())
        if course.comments:
            for i, comment in enumerate(course.comments[:3], 1):
                text = (comment.get("comment", "") or "")[:200]
                if len(comment.get("comment", "") or "") > 200:
                    text += "..."
                semester = comment.get("semester", "?")
                resp.add_field(f"💬 心得 #{i} ({semester})", text or "（無內容）")
        else:
            resp.add_field("💬 心得", "目前沒有心得")
        return resp
