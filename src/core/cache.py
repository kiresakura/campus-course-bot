"""課程快取（純資料/查詢層，無網路、無平台 SDK）。

讀取本地 course_cache.json 並提供搜尋/排行查詢。模糊搜尋依賴 thefuzz，
若該套件未安裝則自動退化為「精確包含比對」，不會讓整個程式無法啟動。
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 模糊搜尋為選用：缺少 thefuzz 時退化為精確比對。
try:
    from thefuzz import fuzz, process  # type: ignore
    _HAS_FUZZ = True
except Exception:  # pragma: no cover - 取決於安裝環境
    _HAS_FUZZ = False
    logger.warning("[Cache] 未安裝 thefuzz，模糊搜尋停用（僅精確比對）")


class CourseCache:
    """記憶體內的課程資料與索引。"""

    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.cache: Dict[str, dict] = {}
        self.by_teacher: Dict[str, List[str]] = {}
        self.by_dept: Dict[str, List[str]] = {}
        self.load()

    # -- 載入 / 儲存 -------------------------------------------------------
    def load(self) -> None:
        if not os.path.exists(self.cache_file):
            logger.warning(
                "[Cache] 找不到 %s，請先執行 build_cache.py 建立快取", self.cache_file
            )
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.cache = data.get("courses", {})
            self.by_teacher = data.get("by_teacher", {})
            self.by_dept = data.get("by_dept", {})
            logger.info("[Cache] 載入 %d 門課程", len(self.cache))
        except Exception:
            logger.exception("[Cache] 載入失敗")

    def save(self) -> None:
        """同步寫檔（呼叫端若在 async 內請用 asyncio.to_thread 包起來）。"""
        os.makedirs(os.path.dirname(self.cache_file) or ".", exist_ok=True)
        payload = {
            "last_updated": datetime.now().isoformat(),
            "courses": self.cache,
            "by_teacher": self.by_teacher,
            "by_dept": self.by_dept,
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("[Cache] 已儲存 %d 門課程", len(self.cache))

    @property
    def is_empty(self) -> bool:
        return not self.cache

    def add_course(self, course: dict) -> None:
        """加入一門課並更新索引（供 build_cache 使用）。"""
        cid = course["id"]
        self.cache[cid] = course
        teacher = course.get("teacher")
        dept = course.get("dept")
        if teacher:
            self.by_teacher.setdefault(teacher, [])
            if cid not in self.by_teacher[teacher]:
                self.by_teacher[teacher].append(cid)
        if dept:
            self.by_dept.setdefault(dept, [])
            if cid not in self.by_dept[dept]:
                self.by_dept[dept].append(cid)

    # -- 查詢 --------------------------------------------------------------
    def search_course(self, keyword: str, limit: int = 20) -> List[dict]:
        if self.is_empty or not keyword:
            return []
        keyword = keyword.lower()

        exact = [
            c
            for c in self.cache.values()
            if keyword in c.get("name", "").lower()
            or keyword in c.get("teacher", "").lower()
            or keyword in c.get("dept", "").lower()
        ]
        if len(exact) >= 5 or not _HAS_FUZZ:
            return sorted(exact, key=lambda x: x.get("rate_count", 0), reverse=True)[:limit]

        choices = {
            cid: f"{c.get('name', '')} {c.get('teacher', '')} {c.get('dept', '')}"
            for cid, c in self.cache.items()
        }
        fuzzy = process.extract(
            keyword, choices, limit=limit, scorer=fuzz.partial_token_sort_ratio
        )
        matched_ids = [res[2] for res in fuzzy if res[1] > 50]

        seen = {c["id"] for c in exact}
        for mid in matched_ids:
            if mid not in seen:
                exact.append(self.cache[mid])
                seen.add(mid)
        return sorted(exact, key=lambda x: x.get("rate_count", 0), reverse=True)[:limit]

    def get_professor_courses(self, name: str) -> List[dict]:
        course_ids = self.by_teacher.get(name)
        if not course_ids and _HAS_FUZZ:
            teachers = list(self.by_teacher.keys())
            best = process.extractOne(name, teachers, scorer=fuzz.token_sort_ratio) if teachers else None
            if best and best[1] > 70:
                course_ids = self.by_teacher[best[0]]
        if course_ids:
            return [self.cache[cid] for cid in course_ids if cid in self.cache]
        return []

    def get_top_sweet(self, limit: int = 10, dept: Optional[str] = None) -> List[dict]:
        courses = self._rated_courses(dept)
        return sorted(courses, key=lambda x: x.get("sweet", 0), reverse=True)[:limit]

    def get_top_cold(self, limit: int = 10, dept: Optional[str] = None) -> List[dict]:
        courses = self._rated_courses(dept)
        return sorted(courses, key=lambda x: x.get("cold", 0), reverse=True)[:limit]

    def get_worst_courses(self, limit: int = 10) -> List[dict]:
        courses = [c for c in self.cache.values() if c.get("rate_count", 0) >= 3]

        def score(c: dict) -> float:
            return (c.get("sweet", 0) + c.get("cold", 0) + c.get("got", 0)) / 3

        return sorted(courses, key=score)[:limit]

    def _rated_courses(self, dept: Optional[str]) -> List[dict]:
        courses = list(self.cache.values())
        if dept:
            courses = [c for c in courses if dept in c.get("dept", "")]
        return [c for c in courses if c.get("rate_count", 0) > 0]
