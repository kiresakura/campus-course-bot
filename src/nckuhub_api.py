"""
NCKUHUB API 封裝模組
提供課程資料查詢、快取管理功能
"""

import aiohttp
import asyncio
import json
import os
import logging
import aiofiles
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from thefuzz import fuzz, process

# 設定日誌
logger = logging.getLogger(__name__)

# 課程資料結構
@dataclass
class Course:
    id: str
    name: str
    dept: str
    teacher: str
    credits: int
    time: str
    classroom: str
    sweet: float      # 甜度
    cold: float       # 涼度
    got: float        # 收穫
    rate_count: int   # 評分人數
    comments: List[Dict] = None

    @classmethod
    def from_api_response(cls, data: dict) -> Optional['Course']:
        """從 NCKUHUB API 回應建立 Course 物件"""
        if not data or 'courseInfo' not in data:
            return None
        
        info = data['courseInfo']
        return cls(
            id=str(info.get('id', '')),
            name=info.get('課程名稱', ''),
            dept=info.get('系所名稱', ''),
            teacher=info.get('老師', ''),
            credits=info.get('學分', 0),
            time=info.get('時間', ''),
            classroom=info.get('教室', ''),
            sweet=float(data.get('sweet', 0) or 0),
            cold=float(data.get('cold', 0) or 0),
            got=float(data.get('got', 0) or 0),
            rate_count=int(data.get('rate_count', 0) or 0),
            comments=data.get('comment', [])
        )
    
    def to_dict(self):
        return asdict(self)


class NCKUHubAPI:
    """NCKUHUB API 客戶端"""
    
    BASE_URL = "https://nckuhub.com/course"
    
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "course_cache.json")
        self.cache: Dict[str, dict] = {}
        self.by_teacher: Dict[str, List[str]] = {}
        self.by_dept: Dict[str, List[str]] = {}
        self._load_cache()
    
    def _load_cache(self):
        """載入本地快取 (同步，僅在初始化時呼叫)"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get('courses', {})
                    self.by_teacher = data.get('by_teacher', {})
                    self.by_dept = data.get('by_dept', {})
                    logger.info(f"[Cache] 載入 {len(self.cache)} 門課程")
            except Exception as e:
                logger.error(f"[Cache] 載入失敗: {e}")
    
    async def _save_cache_async(self):
        """非同步儲存快取到本地"""
        os.makedirs(self.cache_dir, exist_ok=True)
        data = {
            'last_updated': datetime.now().isoformat(),
            'courses': self.cache,
            'by_teacher': self.by_teacher,
            'by_dept': self.by_dept
        }
        try:
            async with aiofiles.open(self.cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            logger.info(f"[Cache] 已儲存 {len(self.cache)} 門課程")
        except Exception as e:
            logger.error(f"[Cache] 儲存失敗: {e}")

    
    async def fetch_course(self, course_id: int) -> Optional[Course]:
        """從 NCKUHUB 抓取單一課程資料"""
        url = f"{self.BASE_URL}/{course_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return Course.from_api_response(data)
        except Exception as e:
            logger.warning(f"[API] 抓取課程 {course_id} 失敗: {e}")
        return None
    
    async def build_cache(self, start_id: int = 1, end_id: int = 15000, concurrency: int = 5):
        """並發掃描並建立課程快取"""
        logger.info(f"[Cache] 開始並發掃描課程 {start_id} ~ {end_id} (並發數: {concurrency})...")
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def fetch_with_semaphore(session, pid):
            async with semaphore:
                try:
                    url = f"{self.BASE_URL}/{pid}"
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            course = Course.from_api_response(data)
                            if course and course.name:
                                return course
                except Exception:
                    pass
                return None

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_with_semaphore(session, i) for i in range(start_id, end_id + 1)]
            
            # 使用 as_completed 或 gather，這裡用 gather 簡單處理，也可以分批處理避免記憶體過大
            # 考慮到 15000 個任務一次 gather 可能會有點多，分批處理更穩健
            batch_size = 100
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch)
                
                for course in results:
                    if course:
                        self.cache[course.id] = {
                            'id': course.id,
                            'name': course.name,
                            'dept': course.dept,
                            'teacher': course.teacher,
                            'time': course.time,
                            'classroom': course.classroom,
                            'sweet': course.sweet,
                            'cold': course.cold,
                            'got': course.got,
                            'rate_count': course.rate_count
                        }
                        # 建立索引
                        if course.teacher:
                            self.by_teacher.setdefault(course.teacher, []).append(course.id)
                        if course.dept:
                            self.by_dept.setdefault(course.dept, []).append(course.id)
                
                logger.info(f"[Cache] 進度: {min(i + batch_size, len(tasks))}/{len(tasks)}...")
                
        await self._save_cache_async()
        logger.info(f"[Cache] 掃描完成！共 {len(self.cache)} 門課程")

    
    def search_course(self, keyword: str, limit: int = 20) -> List[dict]:
        """搜尋課程（支援模糊搜尋）"""
        if not self.cache:
            return []
            
        keyword = keyword.lower()
        results = []
        
        # 1. 精確/包含匹配 (優先)
        exact_matches = []
        for course in self.cache.values():
            if keyword in course['name'].lower() or \
               keyword in course.get('teacher', '').lower() or \
               keyword in course.get('dept', '').lower():
                exact_matches.append(course)
        
        # 如果精確匹配夠多，直接回傳
        if len(exact_matches) >= 5:
             return sorted(exact_matches, key=lambda x: x.get('rate_count', 0), reverse=True)[:limit]

        # 2. 模糊匹配 (當精確匹配太少時啟用)
        # 建立搜尋候選字串： "課程名稱 老師 系所"
        choices = {cid: f"{c['name']} {c['teacher']} {c['dept']}" for cid, c in self.cache.items()}
        
        # 使用 fuzzywuzzy 找出最接近的
        fuzzy_results = process.extract(keyword, choices, limit=limit, scorer=fuzz.partial_token_sort_ratio)
        
        matched_ids = [res[2] for res in fuzzy_results if res[1] > 50] # 分數 > 50 才算
        
        # 合併結果 (精確匹配優先)
        seen_ids = set(c['id'] for c in exact_matches)
        for mid in matched_ids:
            if mid not in seen_ids:
                exact_matches.append(self.cache[mid])
                seen_ids.add(mid)
                
        return sorted(exact_matches, key=lambda x: x.get('rate_count', 0), reverse=True)[:limit]
    
    def get_professor_courses(self, name: str) -> List[dict]:
        """取得某教授的所有課程"""
        # 嘗試精確匹配
        course_ids = self.by_teacher.get(name)
        
        # 如果找不到，嘗試模糊搜尋老師名字
        if not course_ids:
            teachers = list(self.by_teacher.keys())
            best_match = process.extractOne(name, teachers, scorer=fuzz.token_sort_ratio)
            if best_match and best_match[1] > 70:
                course_ids = self.by_teacher[best_match[0]]
        
        if course_ids:
            return [self.cache[cid] for cid in course_ids if cid in self.cache]
        return []
    
    def get_top_sweet(self, limit: int = 10, dept: str = None) -> List[dict]:
        """取得最甜的課程"""
        courses = list(self.cache.values())
        if dept:
            courses = [c for c in courses if dept in c.get('dept', '')]
        courses = [c for c in courses if c.get('rate_count', 0) > 0]
        return sorted(courses, key=lambda x: x.get('sweet', 0), reverse=True)[:limit]
    
    def get_top_cold(self, limit: int = 10, dept: str = None) -> List[dict]:
        """取得最涼的課程"""
        courses = list(self.cache.values())
        if dept:
            courses = [c for c in courses if dept in c.get('dept', '')]
        courses = [c for c in courses if c.get('rate_count', 0) > 0]
        return sorted(courses, key=lambda x: x.get('cold', 0), reverse=True)[:limit]
    
    def get_worst_courses(self, limit: int = 10) -> List[dict]:
        """取得最雷的課程（綜合評分最低）"""
        courses = list(self.cache.values())
        courses = [c for c in courses if c.get('rate_count', 0) >= 3]
        def score(c):
            return (c.get('sweet', 0) + c.get('cold', 0) + c.get('got', 0)) / 3
        return sorted(courses, key=score)[:limit]

if __name__ == "__main__":
    async def test():
        api = NCKUHubAPI()
        # 測試一下搜尋
        print("搜尋 '歷史':", len(api.search_course("歷史")))
        print("搜尋 'lishi' (模糊):", len(api.search_course("lishi")))
    
    asyncio.run(test())

