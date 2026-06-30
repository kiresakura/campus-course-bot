"""NCKUHUB 課程資料抓取客戶端（網路層）。

注意：此處抓取的是第三方網站 nckuhub.com 的資料。請尊重對方服務：
- 帶上可識別的 User-Agent
- 控制並發並加入請求間隔/退避
- 抓下來的資料僅供自行建立本地快取，請勿再散布（見 README / PRIVACY）。
"""

import asyncio
import logging
from typing import Optional

import aiohttp

from .cache import CourseCache
from .models import Course

logger = logging.getLogger(__name__)


class NCKUHubClient:
    BASE_URL = "https://nckuhub.com/course"
    # 可識別的 User-Agent，方便對方辨識流量來源。
    USER_AGENT = (
        "campus-course-bot/1.0 (self-hosted course-review bot; "
        "https://github.com/kiresakura/campus-course-bot)"
    )
    REQUEST_DELAY = 0.5  # 每個請求之間的禮貌性間隔（秒）

    def __init__(self, cache: CourseCache):
        self.cache = cache

    def _headers(self) -> dict:
        return {"User-Agent": self.USER_AGENT}

    async def fetch_course(
        self,
        course_id: int,
        session: Optional[aiohttp.ClientSession] = None,
        retries: int = 3,
    ) -> Optional[Course]:
        """抓取單一課程；失敗時做指數退避重試。"""
        own_session = session is None
        if own_session:
            session = aiohttp.ClientSession(headers=self._headers())
        url = f"{self.BASE_URL}/{course_id}"
        try:
            for attempt in range(retries):
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            return Course.from_api_response(await resp.json())
                        if resp.status == 404:
                            return None
                        logger.warning("[API] 課程 %s 狀態碼 %s", course_id, resp.status)
                except Exception:
                    logger.warning("[API] 抓取課程 %s 第 %d 次失敗", course_id, attempt + 1)
                await asyncio.sleep(self.REQUEST_DELAY * (2 ** attempt))  # 退避
            return None
        finally:
            if own_session:
                await session.close()

    async def build_cache(
        self, start_id: int = 1, end_id: int = 15000, concurrency: int = 5
    ) -> int:
        """並發掃描課程並建立本地快取，回傳總課程數。"""
        logger.info(
            "[Cache] 開始掃描課程 %d ~ %d（並發 %d）", start_id, end_id, concurrency
        )
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_one(session: aiohttp.ClientSession, pid: int) -> Optional[Course]:
            async with semaphore:
                course = await self.fetch_course(pid, session=session, retries=2)
                await asyncio.sleep(self.REQUEST_DELAY)  # 禮貌性間隔
                return course if (course and course.name) else None

        async with aiohttp.ClientSession(headers=self._headers()) as session:
            ids = list(range(start_id, end_id + 1))
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch = ids[i : i + batch_size]
                results = await asyncio.gather(*(fetch_one(session, pid) for pid in batch))
                for course in results:
                    if course:
                        self.cache.add_course(
                            {
                                "id": course.id,
                                "name": course.name,
                                "dept": course.dept,
                                "teacher": course.teacher,
                                "time": course.time,
                                "classroom": course.classroom,
                                "sweet": course.sweet,
                                "cold": course.cold,
                                "got": course.got,
                                "rate_count": course.rate_count,
                            }
                        )
                logger.info("[Cache] 進度 %d/%d", min(i + batch_size, len(ids)), len(ids))

        await asyncio.to_thread(self.cache.save)
        logger.info("[Cache] 掃描完成，共 %d 門課程", len(self.cache.cache))
        return len(self.cache.cache)
