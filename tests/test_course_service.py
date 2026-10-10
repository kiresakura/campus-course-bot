"""CourseService behavior tests (pure logic, no network).

Assertions check the production UI strings, which are intentionally Chinese.
"""

import asyncio
import json

from core.course_service import CourseService, _score_bar, _score_emoji
from core.models import BotResponse, Course, ResponseStyle


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


# --------------------------------------------------------------------------
# Query / ranking / compare details
# --------------------------------------------------------------------------
def _write_cache(path, courses):
    """Write a minimal cache file in the format build_cache.py produces."""
    by_teacher, by_dept = {}, {}
    for c in courses:
        by_teacher.setdefault(c["teacher"], []).append(c["id"])
        by_dept.setdefault(c["dept"], []).append(c["id"])
    data = {"courses": {c["id"]: c for c in courses}, "by_teacher": by_teacher, "by_dept": by_dept}
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _course(cid, name, teacher="T", rate_count=5):
    return {"id": cid, "name": name, "dept": "D", "teacher": teacher,
            "sweet": 5.0, "cold": 5.0, "got": 5.0, "rate_count": rate_count}


def test_search_lists_at_most_ten_courses(tmp_path):
    path = _write_cache(tmp_path / "c.json", [_course(str(i), f"Course {i}") for i in range(12)])
    resp = CourseService(path).search("course")
    assert resp.description == "找到 12 門課程"
    assert len(resp.fields) == 10


def test_search_result_shows_scores_and_detail_hint(service):
    value = service.search("微積分").fields[0].value
    assert "🍬 `8.0` 🛋️ `6.0` 📖 `9.0` ｜ 👥 10" in value
    assert "/詳細 1" in value


def test_professor_shows_average_scores(service):
    resp = service.professor("王小明")  # 微積分 (8, 6, 9) + 程式設計 (7, 4, 8)
    assert resp.fields[0].name == "📊 平均評分"
    assert resp.fields[0].value == "🍬 `7.5` ｜ 🛋️ `5.0` ｜ 📖 `8.5`"
    assert {f.name for f in resp.fields[1:]} == {"微積分", "程式設計"}


def test_professor_lists_five_courses_and_counts_the_rest(tmp_path):
    path = _write_cache(tmp_path / "c.json", [_course(str(i), f"Course {i}", teacher="Lin") for i in range(7)])
    resp = CourseService(path).professor("Lin")
    assert len(resp.fields) == 1 + 5  # averages + five courses
    assert resp.footer == "還有 2 門課程未顯示"


def test_professor_not_found(service):
    resp = service.professor("完全不存在的老師zzz")
    assert resp.style == ResponseStyle.WARNING


def test_top_sweet_filters_by_dept(service):
    resp = service.top_sweet("資訊系")
    assert [f.name for f in resp.fields] == ["🥇 程式設計"]
    assert "評分: `7.0`" in resp.fields[0].value


def test_ranking_with_unknown_dept_warns(service):
    assert service.top_sweet("不存在的系").style == ResponseStyle.WARNING
    assert service.top_cold("不存在的系").style == ResponseStyle.WARNING


def test_ranking_uses_medals_for_top_three(service):
    names = [f.name for f in service.top_sweet().fields]
    assert names == ["🥇 微積分", "🥈 程式設計", "🥉 大學英文", "　 冷門課"]


def test_worst_limit_is_clamped(service):
    assert len(service.worst(0).fields) == 1
    assert len(service.worst(2).fields) == 2
    assert len(service.worst(99).fields) == 4  # every course with >= 3 ratings


def test_worst_scores_are_averages(service):
    # 冷門課: (2 + 3 + 2) / 3
    assert "評分: `2.3`" in service.worst(1).fields[0].value


def test_compare_counts_wins_per_category(service):
    # 微積分 (8, 6, 9) vs 大學英文 (5, 9, 4): sweet A, easy B, takeaway A
    resp = service.compare("微積分", "大學英文")
    rows = {f.name: f.value for f in resp.fields}
    assert rows["🍬 甜度"] == "`8.0` ⬅️ `5.0`"
    assert rows["🛋️ 涼度"] == "`6.0` ➡️ `9.0`"
    assert rows["📖 收穫"] == "`9.0` ⬅️ `4.0`"
    assert rows["📊 結果"] == "🏆 **微積分** 勝出！"


def test_compare_same_course_is_a_tie(service):
    rows = {f.name: f.value for f in service.compare("微積分", "微積分").fields}
    assert rows["🍬 甜度"] == "`8.0` 🤝 `8.0`"
    assert rows["📊 結果"] == "🤝 平手！"


def test_compare_lists_every_missing_course(service):
    resp = service.compare("不存在甲zzz", "不存在乙zzz")
    assert resp.description == "找不到：不存在甲zzz, 不存在乙zzz"


# --------------------------------------------------------------------------
# Detail (network layer stubbed out)
# --------------------------------------------------------------------------
def _stub_fetch(service, monkeypatch, result=None, error=None):
    async def fake_fetch(*args, **kwargs):
        if error:
            raise error
        return result

    monkeypatch.setattr(service.client, "fetch_course", fake_fetch)


def test_detail_shows_card_and_first_three_comments(service, monkeypatch):
    comments = [{"comment": "很棒", "semester": "113-1"}, {"comment": "x" * 250, "semester": "113-2"},
                {"comment": "", "semester": "112-2"}, {"comment": "第四則不顯示", "semester": "112-1"}]
    course = Course(id="7", name="測試課", dept="測試系", teacher="測試老師",
                    sweet=8.0, cold=6.0, got=9.0, rate_count=3, comments=comments)
    _stub_fetch(service, monkeypatch, result=course)
    resp = asyncio.run(service.detail(7))
    rows = {f.name: f.value for f in resp.fields}
    assert resp.title == "📚 測試課" and resp.footer == "課程 ID: 7"
    assert rows["🍬 甜度"] == "`8.0/10` ████████░░ 🔥"
    assert rows["💬 心得 #1 (113-1)"] == "很棒"
    assert rows["💬 心得 #2 (113-2)"] == "x" * 200 + "..."  # long comments are truncated
    assert rows["💬 心得 #3 (112-2)"] == "（無內容）"
    assert "第四則不顯示" not in resp.to_markdown()


def test_detail_without_comments(service, monkeypatch):
    _stub_fetch(service, monkeypatch, result=Course(id="7", name="n", dept="d", teacher="t"))
    rows = {f.name: f.value for f in asyncio.run(service.detail(7)).fields}
    assert rows["💬 心得"] == "目前沒有心得"


def test_detail_fetch_error_hides_exception_text(service, monkeypatch):
    _stub_fetch(service, monkeypatch, error=RuntimeError("internal secret detail"))
    resp = asyncio.run(service.detail(7))
    assert resp.style == ResponseStyle.WARNING
    assert "暫時無法查詢" in resp.title
    assert "secret" not in resp.to_markdown()


# --------------------------------------------------------------------------
# Score helpers
# --------------------------------------------------------------------------
def test_score_bar_is_clamped_to_ten_cells():
    assert _score_bar(8.5) == "████████░░"
    assert _score_bar(15) == "██████████"
    assert _score_bar(-3) == "░░░░░░░░░░"


def test_score_emoji_thresholds():
    assert [_score_emoji(s) for s in (8, 7.9, 6, 5.9, 4, 3.9)] == ["🔥", "✨", "✨", "😐", "😐", "💀"]
