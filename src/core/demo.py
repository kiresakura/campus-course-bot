"""Offline demo mode: the bundled fictional dataset, served without network access.

examples/fictional_courses.json holds invented courses, instructors, ratings and
comments (not scraped; no real course or person). It lets you try every command
without building a cache or contacting the data source.
"""

import os
from dataclasses import fields
from typing import Optional

from .cache import CourseCache
from .course_service import CourseService
from .models import Course

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEMO_CACHE_FILE = os.path.join(PROJECT_ROOT, "examples", "fictional_courses.json")

_COURSE_FIELDS = {f.name for f in fields(Course)}


class OfflineCourseClient:
    """Stand-in for NCKUHubClient: course details come from the local file, not the network."""

    def __init__(self, cache: CourseCache):
        self.cache = cache

    async def fetch_course(self, course_id: int) -> Optional[Course]:
        data = self.cache.cache.get(str(course_id))
        if not data:
            return None
        return Course(**{k: v for k, v in data.items() if k in _COURSE_FIELDS})


def build_demo_service() -> CourseService:
    """CourseService over the fictional dataset that never touches the network."""
    service = CourseService(DEMO_CACHE_FILE)
    service.client = OfflineCourseClient(service.cache)
    return service
