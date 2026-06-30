"""CourseService behavior tests (pure logic, no network).

Assertions check the production UI strings, which are intentionally Chinese.
"""

import asyncio

from core.models import BotResponse, ResponseStyle


def test_search_finds_course(service):
    resp = service.search("微積分")
    assert isinstance(resp, BotResponse)
    assert "搜尋結果" in resp.title
    assert any("微積分" in f.name for f in resp.fields)


def test_search_by_teacher(service):
    resp = service.search("王小明")
    # 王小明 teaches two courses (微積分, 程式設計)
    names = " ".join(f.name for f in resp.fields)
    assert "微積分" in names and "程式設計" in names


def test_search_not_found(service):
    resp = service.search("不存在的課程xyz")
    assert resp.style == ResponseStyle.WARNING
    assert "找不到" in resp.title


def test_professor_average(service):
    resp = service.professor("王小明")
    assert "王小明" in resp.title
    assert "共有 2 門課程" in resp.description


def test_top_sweet_orders_by_sweet(service):
    resp = service.top_sweet()
    assert resp.style == ResponseStyle.SWEET
    # sweetest is 微積分 (8.0)
    assert "微積分" in resp.fields[0].name


def test_top_cold_orders_by_cold(service):
    resp = service.top_cold()
    assert resp.style == ResponseStyle.COLD
    # easiest is 大學英文 (9.0)
    assert "大學英文" in resp.fields[0].name


def test_worst_has_disclaimer(service):
    resp = service.worst()
    assert resp.style == ResponseStyle.DANGER
    assert "僅供參考" in resp.footer
    # worst is 冷門課 (lowest average with rate_count>=3)
    assert "冷門課" in resp.fields[0].name


def test_compare_picks_winner(service):
    resp = service.compare("微積分", "大學英文")
    assert resp.title == "⚔️ 課程 PK"
    assert any(f.name == "📊 結果" for f in resp.fields)


def test_compare_missing(service):
    resp = service.compare("微積分", "完全不存在zzz")
    assert resp.style == ResponseStyle.WARNING


def test_detail_not_found(service, monkeypatch):
    async def fake_fetch(*args, **kwargs):
        return None

    monkeypatch.setattr(service.client, "fetch_course", fake_fetch)
    resp = asyncio.run(service.detail(999999))
    assert resp.style == ResponseStyle.DANGER
    assert "找不到" in resp.title
