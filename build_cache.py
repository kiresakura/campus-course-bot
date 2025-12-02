"""
課程快取建立腳本
掃描 NCKUHUB 課程 ID 並建立本地快取
"""

import asyncio
import sys
sys.path.insert(0, 'src')
from nckuhub_api import NCKUHubAPI

async def main():
    api = NCKUHubAPI(cache_dir='data')

    # 找出目前最大的 ID
    if api.cache:
        max_id = max(int(k) for k in api.cache.keys())
        start_from = max_id + 1
    else:
        start_from = 1

    print(f"[Info] 目前快取: {len(api.cache)} 門課程, 從 ID {start_from} 開始")

    # 繼續掃描到 15000
    await api.build_cache(start_id=start_from, end_id=15000, delay=0.15)

    print(f"\n✅ 快取建立完成！")
    print(f"📊 共 {len(api.cache)} 門課程")
    print(f"👨‍🏫 共 {len(api.by_teacher)} 位教授")
    print(f"🏫 共 {len(api.by_dept)} 個系所")

if __name__ == "__main__":
    asyncio.run(main())
