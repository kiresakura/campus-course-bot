"""Cache-building script: scan NCKUHUB course IDs and build a local cache.

Note: the fetched data is for building your *own* local cache only. Do not
redistribute or upload data/course_cache.json to a public repo (it is already
excluded via .gitignore). See PRIVACY.md.
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

    print(f"[info] current cache has {len(cache.cache)} courses; starting from ID {start_from}")

    total = await client.build_cache(start_id=start_from, end_id=15000, concurrency=5)

    print("\n[done] cache build complete")
    print(f"  courses:     {total}")
    print(f"  professors:  {len(cache.by_teacher)}")
    print(f"  departments: {len(cache.by_dept)}")


if __name__ == "__main__":
    asyncio.run(main())
