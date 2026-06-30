"""課程快取建立腳本：掃描 NCKUHUB 課程 ID 並建立本地快取。

注意：抓下來的資料僅供你「自行建立本地快取」使用。請勿將 data/course_cache.json
再次散布或上傳到公開倉庫（已於 .gitignore 排除）。詳見 PRIVACY.md。
"""

import asyncio
import os
import sys

sys.path.insert(0, "src")

from core.cache import CourseCache
from core.nckuhub_client import NCKUHubClient

CACHE_FILE = os.path.join("data", "course_cache.json")


async def main():
    cache = CourseCache(CACHE_FILE)
    client = NCKUHubClient(cache)

    if cache.cache:
        start_from = max(int(k) for k in cache.cache.keys()) + 1
    else:
        start_from = 1

    print(f"[Info] 目前快取 {len(cache.cache)} 門課程，從 ID {start_from} 開始")

    total = await client.build_cache(start_id=start_from, end_id=15000, concurrency=5)

    print("\n✅ 快取建立完成！")
    print(f"📊 共 {total} 門課程")
    print(f"👨‍🏫 共 {len(cache.by_teacher)} 位教授")
    print(f"🏫 共 {len(cache.by_dept)} 個系所")


if __name__ == "__main__":
    asyncio.run(main())
