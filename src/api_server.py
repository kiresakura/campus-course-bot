"""
NCKUHUB REST API Server
使用 FastAPI 包裝 NCKUHubAPI
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

from nckuhub_api import NCKUHubAPI, Course

app = FastAPI(
    title="NCKUHUB API",
    description="成功大學課程評價查詢 API",
    version="1.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 API 客戶端（Railway 執行時工作目錄是 src/，所以要指向上層的 data/）
import os
cache_dir = "../data" if os.path.exists("../data") else "data"
api = NCKUHubAPI(cache_dir=cache_dir)


# Response Models
class CourseBasic(BaseModel):
    id: str
    name: str
    dept: str
    teacher: str
    time: Optional[str] = ""
    classroom: Optional[str] = ""
    sweet: float
    cold: float
    got: float
    rate_count: int


class CourseDetail(CourseBasic):
    credits: int
    comments: Optional[List[dict]] = None


class SearchResponse(BaseModel):
    count: int
    courses: List[CourseBasic]


class DeptResponse(BaseModel):
    count: int
    departments: List[str]


# API Endpoints

@app.get("/")
async def root():
    """API 根路徑"""
    return {
        "name": "NCKUHUB API",
        "version": "1.0.0",
        "endpoints": ["/search", "/alldept", "/course/{id}"]
    }


@app.get("/search", response_model=SearchResponse)
async def search_courses(
    q: str = Query(..., description="搜尋關鍵字（課程名稱、教師、系所）"),
    limit: int = Query(20, ge=1, le=100, description="回傳筆數上限")
):
    """
    搜尋課程

    支援模糊搜尋，可搜尋課程名稱、教師姓名、系所名稱
    """
    results = api.search_course(q, limit=limit)
    return SearchResponse(
        count=len(results),
        courses=[CourseBasic(**c) for c in results]
    )


@app.get("/alldept", response_model=DeptResponse)
async def get_all_departments():
    """
    取得所有系所列表
    """
    departments = sorted(api.by_dept.keys())
    return DeptResponse(
        count=len(departments),
        departments=departments
    )


@app.get("/course/{course_id}", response_model=CourseDetail)
async def get_course(course_id: str):
    """
    取得單一課程詳細資料

    包含完整課程資訊與評論
    """
    # 先從快取找
    if course_id in api.cache:
        cached = api.cache[course_id]
        # 快取只有基本資料，需要從 API 取得完整資料（包含評論）
        course = await api.fetch_course(int(course_id))
        if course:
            return CourseDetail(
                id=course.id,
                name=course.name,
                dept=course.dept,
                teacher=course.teacher,
                time=course.time,
                classroom=course.classroom,
                credits=course.credits,
                sweet=course.sweet,
                cold=course.cold,
                got=course.got,
                rate_count=course.rate_count,
                comments=course.comments
            )

    # 快取沒有，直接從 API 取得
    course = await api.fetch_course(int(course_id))
    if not course:
        raise HTTPException(status_code=404, detail=f"課程 {course_id} 不存在")

    return CourseDetail(
        id=course.id,
        name=course.name,
        dept=course.dept,
        teacher=course.teacher,
        time=course.time,
        classroom=course.classroom,
        credits=course.credits,
        sweet=course.sweet,
        cold=course.cold,
        got=course.got,
        rate_count=course.rate_count,
        comments=course.comments
    )


@app.get("/top/sweet")
async def get_top_sweet(
    limit: int = Query(10, ge=1, le=50),
    dept: Optional[str] = Query(None, description="篩選系所")
):
    """取得最甜課程排行"""
    results = api.get_top_sweet(limit=limit, dept=dept)
    return {"count": len(results), "courses": results}


@app.get("/top/cold")
async def get_top_cold(
    limit: int = Query(10, ge=1, le=50),
    dept: Optional[str] = Query(None, description="篩選系所")
):
    """取得最涼課程排行"""
    results = api.get_top_cold(limit=limit, dept=dept)
    return {"count": len(results), "courses": results}


@app.get("/professor/{name}")
async def get_professor_courses(name: str):
    """取得某教授的所有課程"""
    results = api.get_professor_courses(name)
    if not results:
        raise HTTPException(status_code=404, detail=f"找不到教授: {name}")
    return {"count": len(results), "courses": results}


@app.post("/cache/rebuild")
async def rebuild_cache(
    start_id: int = Query(1),
    end_id: int = Query(15000),
    concurrency: int = Query(5, ge=1, le=20)
):
    """
    重建課程快取（管理用）

    警告：這個操作會花費很長時間
    """
    await api.build_cache(start_id=start_id, end_id=end_id, concurrency=concurrency)
    return {"message": "快取重建完成", "total_courses": len(api.cache)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
