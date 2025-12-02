"""
NCKUHUB API 封裝模組
提供課程資料查詢、快取管理功能
"""

import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

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


class NCKUHubAPI:
    """NCKUHUB API 客戶端"""
    
    BASE_URL = "https://nckuhub.com/course"
    CACHE_FILE = "data/course_cache.json"
    
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "course_cache.json")
        self.cache: Dict[str, dict] = {}
        self.by_teacher: Dict[str, List[str]] = {}
        self.by_dept: Dict[str, List[str]] = {}
        self._load_cache()
    
    def _load_cache(self):
        """載入本地快取"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get('courses', {})
                    self.by_teacher = data.get('by_teacher', {})
                    self.by_dept = data.get('by_dept', {})
                    print(f"[Cache] 載入 {len(self.cache)} 門課程")
            except Exception as e:
                print(f"[Cache] 載入失敗: {e}")
    
    def _save_cache(self):
        """儲存快取到本地"""
        os.makedirs(self.cache_dir, exist_ok=True)
        data = {
            'last_updated': datetime.now().isoformat(),
            'courses': self.cache,
            'by_teacher': self.by_teacher,
            'by_dept': self.by_dept
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Cache] 已儲存 {len(self.cache)} 門課程")

    
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
            print(f"[API] 抓取課程 {course_id} 失敗: {e}")
        return None
    
    async def build_cache(self, start_id: int = 1, end_id: int = 15000, delay: float = 0.3):
        """掃描並建立課程快取（耗時操作，建議背景執行）"""
        print(f"[Cache] 開始掃描課程 {start_id} ~ {end_id}...")
        
        async with aiohttp.ClientSession() as session:
            for course_id in range(start_id, end_id + 1):
                try:
                    url = f"{self.BASE_URL}/{course_id}"
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            course = Course.from_api_response(data)
                            if course and course.name:
                                # 儲存到快取
                                self.cache[course.id] = {
                                    'id': course.id,
                                    'name': course.name,
                                    'dept': course.dept,
                                    'teacher': course.teacher,
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
                                
                                if len(self.cache) % 100 == 0:
                                    print(f"[Cache] 已掃描 {len(self.cache)} 門課程...")
                                    self._save_cache()  # 定期儲存
                                    
                except Exception as e:
                    pass  # 靜默處理錯誤，繼續掃描
                
                await asyncio.sleep(delay)  # Rate limiting
        
        self._save_cache()
        print(f"[Cache] 掃描完成！共 {len(self.cache)} 門課程")

    
    def search_course(self, keyword: str, limit: int = 10) -> List[dict]:
        """搜尋課程（從快取）"""
        keyword = keyword.lower()
        results = []
        for course in self.cache.values():
            if keyword in course['name'].lower() or \
               keyword in course.get('teacher', '').lower() or \
               keyword in course.get('dept', '').lower():
                results.append(course)
        # 按評分人數排序
        return sorted(results, key=lambda x: x.get('rate_count', 0), reverse=True)[:limit]
    
    def get_professor_courses(self, name: str) -> List[dict]:
        """取得某教授的所有課程"""
        course_ids = self.by_teacher.get(name, [])
        return [self.cache[cid] for cid in course_ids if cid in self.cache]
    
    def get_top_sweet(self, limit: int = 10, dept: str = None) -> List[dict]:
        """取得最甜的課程"""
        courses = list(self.cache.values())
        if dept:
            courses = [c for c in courses if dept in c.get('dept', '')]
        # 過濾掉沒有評分的課程
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
        courses = [c for c in courses if c.get('rate_count', 0) >= 3]  # 至少3人評分才算
        # 計算綜合分數
        def score(c):
            return (c.get('sweet', 0) + c.get('cold', 0) + c.get('got', 0)) / 3
        return sorted(courses, key=score)[:limit]


# 測試用
if __name__ == "__main__":
    async def test():
        api = NCKUHubAPI()
        course = await api.fetch_course(1)
        if course:
            print(f"課程: {course.name}")
            print(f"教授: {course.teacher}")
            print(f"甜度: {course.sweet} / 涼度: {course.cold} / 收穫: {course.got}")
    
    asyncio.run(test())
