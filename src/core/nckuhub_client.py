"""NCKUHUB course-data fetch client (network layer).

Note: this fetches data from the third-party site nckuhub.com. Be respectful:
- send an identifying User-Agent
- limit concurrency and add request spacing / backoff
- the fetched data is only for building your own local cache — do not
  redistribute it (see README / PRIVACY).
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
    # Identifying User-Agent so the source can attribute the traffic.
    USER_AGENT = (
        "campus-course-bot/1.0 (self-hosted course-review bot; "
        "https://github.com/kiresakura/campus-course-bot)"
    )
    REQUEST_DELAY = 0.5  # courtesy delay between requests (seconds)

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
        """Fetch a single course; retry with exponential backoff on failure."""
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
                        logger.warning("[API] course %s status %s", course_id, resp.status)
                except Exception:
                    logger.warning("[API] fetch course %s attempt %d failed", course_id, attempt + 1)
                await asyncio.sleep(self.REQUEST_DELAY * (2 ** attempt))  # backoff
            return None
        finally:
            if own_session:
                await session.close()

    async def build_cache(
        self, start_id: int = 1, end_id: int = 15000, concurrency: int = 5
    ) -> int:
        """Concurrently scan courses and build the local cache; return the total count."""
        logger.info(
            "[Cache] scanning courses %d ~ %d (concurrency %d)", start_id, end_id, concurrency
        )
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_one(session: aiohttp.ClientSession, pid: int) -> Optional[Course]:
            async with semaphore:
                course = await self.fetch_course(pid, session=session, retries=2)
                await asyncio.sleep(self.REQUEST_DELAY)  # courtesy delay
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
                logger.info("[Cache] progress %d/%d", min(i + batch_size, len(ids)), len(ids))

        await asyncio.to_thread(self.cache.save)
        logger.info("[Cache] scan complete, %d courses total", len(self.cache.cache))
        return len(self.cache.cache)
