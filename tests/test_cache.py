"""CourseCache tests: loading, indexing, search and ranking queries (no network)."""

import json

import pytest

import core.cache as cache_module
from core.cache import CourseCache

needs_fuzz = pytest.mark.skipif(not cache_module._HAS_FUZZ, reason="thefuzz not installed")


def _course(cid, name, teacher="T", dept="D", sweet=5.0, cold=5.0, got=5.0, rate_count=5):
    return {
        "id": cid, "name": name, "dept": dept, "teacher": teacher,
        "sweet": sweet, "cold": cold, "got": got, "rate_count": rate_count,
    }


@pytest.fixture
def make_cache(tmp_path):
    def make(*courses):
        cache = CourseCache(str(tmp_path / "cache.json"))  # file absent: starts empty
        for course in courses:
            cache.add_course(course)
        return cache

    return make


# ------------------------------ load / save -------------------------------
def test_missing_file_gives_empty_cache(tmp_path):
    cache = CourseCache(str(tmp_path / "missing.json"))
    assert cache.is_empty
    assert cache.search_course("anything") == []


def test_corrupt_file_is_ignored(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{not json", encoding="utf-8")
    assert CourseCache(str(path)).is_empty


def test_save_then_load_round_trips(make_cache, tmp_path):
    cache = make_cache(_course("1", "A", teacher="X", dept="D1"), _course("2", "B", teacher="X", dept="D2"))
    cache.save()
    saved = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert "last_updated" in saved
    reloaded = CourseCache(str(tmp_path / "cache.json"))
    assert reloaded.cache == cache.cache
    assert reloaded.by_teacher == {"X": ["1", "2"]}
    assert reloaded.by_dept == {"D1": ["1"], "D2": ["2"]}


def test_add_course_does_not_duplicate_index_entries(make_cache):
    cache = make_cache(_course("1", "A", teacher="X"), _course("1", "A", teacher="X"))
    assert cache.by_teacher == {"X": ["1"]}
    assert cache.by_dept == {"D": ["1"]}


# --------------------------------- search ---------------------------------
def test_search_matches_name_teacher_and_dept_case_insensitively(make_cache, monkeypatch):
    monkeypatch.setattr(cache_module, "_HAS_FUZZ", False)  # isolate the exact-substring pass
    cache = make_cache(
        _course("1", "Data Structures", teacher="Lin", dept="資訊系 CSIE"),
        _course("2", "Poetry", teacher="Wu", dept="中文系 CHIN"),
    )
    assert [c["id"] for c in cache.search_course("structures")] == ["1"]
    assert [c["id"] for c in cache.search_course("WU")] == ["2"]
    assert [c["id"] for c in cache.search_course("csie")] == ["1"]


def test_search_orders_by_rating_count_and_respects_limit(make_cache):
    cache = make_cache(*[_course(str(i), f"Course {i}", rate_count=i) for i in range(1, 8)])
    results = cache.search_course("course", limit=3)
    assert [c["id"] for c in results] == ["7", "6", "5"]


def test_search_with_empty_keyword_returns_nothing(make_cache):
    assert make_cache(_course("1", "A")).search_course("") == []


def test_search_without_thefuzz_uses_exact_matches_only(make_cache, monkeypatch):
    monkeypatch.setattr(cache_module, "_HAS_FUZZ", False)
    cache = make_cache(_course("1", "Calculus I"), _course("2", "Calculus II"))
    assert [c["id"] for c in cache.search_course("Calculus I")] == ["1", "2"]  # substring of both
    assert cache.search_course("Calculsu") == []  # typo: no fuzzy fallback


@needs_fuzz
def test_search_falls_back_to_fuzzy_matching(make_cache):
    cache = make_cache(_course("1", "Calculus"), _course("2", "Poetry"))
    assert [c["id"] for c in cache.search_course("Calculsu")] == ["1"]


# -------------------------------- professor -------------------------------
def test_professor_exact_match(make_cache):
    cache = make_cache(_course("1", "A", teacher="Lin"), _course("2", "B", teacher="Lin"), _course("3", "C", teacher="Wu"))
    assert [c["id"] for c in cache.get_professor_courses("Lin")] == ["1", "2"]


@needs_fuzz
def test_professor_fuzzy_match_tolerates_typos(make_cache):
    cache = make_cache(_course("1", "A", teacher="Margaret"), _course("2", "B", teacher="Zhou"))
    assert [c["id"] for c in cache.get_professor_courses("Margeret")] == ["1"]


def test_professor_unknown_returns_empty(make_cache, monkeypatch):
    monkeypatch.setattr(cache_module, "_HAS_FUZZ", False)
    assert make_cache(_course("1", "A", teacher="Lin")).get_professor_courses("Nobody") == []


# -------------------------------- rankings --------------------------------
def test_top_sweet_and_cold_sort_descending(make_cache):
    cache = make_cache(
        _course("1", "A", sweet=6.0, cold=9.0),
        _course("2", "B", sweet=9.0, cold=1.0),
        _course("3", "C", sweet=7.5, cold=5.0),
    )
    assert [c["id"] for c in cache.get_top_sweet()] == ["2", "3", "1"]
    assert [c["id"] for c in cache.get_top_cold(limit=2)] == ["1", "3"]


def test_rankings_skip_unrated_courses_and_filter_by_dept(make_cache):
    cache = make_cache(
        _course("1", "A", dept="資訊系 CSIE", sweet=9.0),
        _course("2", "B", dept="資訊系 CSIE", sweet=10.0, rate_count=0),  # no ratings yet
        _course("3", "C", dept="中文系 CHIN", sweet=8.0),
    )
    assert [c["id"] for c in cache.get_top_sweet()] == ["1", "3"]
    assert [c["id"] for c in cache.get_top_sweet(dept="資訊")] == ["1"]
    assert [c["id"] for c in cache.get_top_cold(dept="中文")] == ["3"]


def test_worst_needs_three_ratings_and_sorts_by_average(make_cache):
    cache = make_cache(
        _course("1", "A", sweet=1.0, cold=1.0, got=1.0, rate_count=2),  # too few ratings
        _course("2", "B", sweet=3.0, cold=3.0, got=3.0, rate_count=3),
        _course("3", "C", sweet=2.0, cold=2.0, got=2.0, rate_count=10),
        _course("4", "D", sweet=9.0, cold=9.0, got=9.0, rate_count=10),
    )
    assert [c["id"] for c in cache.get_worst_courses()] == ["3", "2", "4"]
    assert [c["id"] for c in cache.get_worst_courses(limit=1)] == ["3"]
