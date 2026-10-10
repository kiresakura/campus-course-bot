"""Offline demo mode tests: the bundled fictional dataset and the --demo entrypoint.

Any attempt to open an HTTP session fails the test, proving the demo never needs
the network. Chinese strings are production UI strings the code returns."""

import asyncio
import io

import pytest

import run
from core.demo import OfflineCourseClient, build_demo_service
from core.models import ResponseStyle


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("demo mode must not open an HTTP session")

    monkeypatch.setattr("core.nckuhub_client.aiohttp.ClientSession", refuse)


@pytest.fixture
def demo():
    return build_demo_service()


def test_demo_indexes_match_the_courses(demo):
    courses = demo.cache.cache
    assert len(courses) >= 10
    for cid, course in courses.items():
        assert course["id"] == cid
        assert cid in demo.cache.by_teacher[course["teacher"]]
        assert cid in demo.cache.by_dept[course["dept"]]
    indexed = [cid for ids in demo.cache.by_teacher.values() for cid in ids]
    assert sorted(indexed) == sorted(courses)


def test_demo_serves_details_offline(demo, no_network):
    assert isinstance(demo.client, OfflineCourseClient)
    resp = asyncio.run(demo.detail(101))
    assert resp.title == "📚 龍類飼育學 Dragon Husbandry"
    assert any(f.name.startswith("💬 心得 #1") and f.value.endswith("...") for f in resp.fields)


def test_demo_detail_for_unknown_id(demo, no_network):
    resp = asyncio.run(demo.detail(999))
    assert resp.style == ResponseStyle.DANGER


def test_demo_answers_every_command(demo):
    assert demo.search("dragon").fields[0].name == "1. 龍類飼育學 Dragon Husbandry"
    assert demo.professor("Ember").description == "共有 2 門課程"
    assert demo.top_sweet().fields[0].name == "🥇 貓語會話（一） Conversational Cat I"
    assert demo.top_cold("鍊金").fields[0].name == "🥇 隱形墨水化學 Invisible Ink Chemistry"
    assert "勝出" in demo.compare("dragon", "unicorn").to_markdown()
    assert demo.worst(1).fields[0].name == "🥇 小行星採礦實習 Asteroid Mining Practicum"


def test_run_demo_in_the_terminal(monkeypatch, capsys, no_network):
    monkeypatch.setattr("sys.stdin", io.StringIO("search time\ndetail 110\n"))
    assert run.main(["--platform", "cli", "--demo"]) == 0
    out = capsys.readouterr().out
    assert "時光旅行倫理學 Ethics of Time Travel" in out
    assert "📚 貓語會話（一） Conversational Cat I" in out
