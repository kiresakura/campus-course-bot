"""Data model and neutral response model tests (pure logic, no network).

The Chinese keys below are the actual NCKUHUB API field names."""

from core.models import BotResponse, Course, ResponseStyle


def _api_payload(**overrides) -> dict:
    payload = {
        "got": "8.0",
        "cold": "7.0",
        "sweet": "9.0",
        "rate_count": 5,
        "courseInfo": {
            "id": 1234,
            "系所名稱": "測試系 TEST",
            "課程名稱": "測試課程",
            "老師": "測試老師",
            "學分": 3,
            "時間": "[1]2~4",
            "教室": "A101",
        },
        "comment": [{"comment": "不錯", "semester": "113-1"}],
    }
    payload.update(overrides)
    return payload


def test_from_api_response_maps_fields():
    course = Course.from_api_response(_api_payload())
    assert course.id == "1234"  # ids are normalised to str
    assert (course.name, course.dept, course.teacher) == ("測試課程", "測試系 TEST", "測試老師")
    assert (course.credits, course.time, course.classroom) == (3, "[1]2~4", "A101")
    # scores arrive as strings and are parsed to float
    assert (course.sweet, course.cold, course.got) == (9.0, 7.0, 8.0)
    assert course.rate_count == 5
    assert course.comments == [{"comment": "不錯", "semester": "113-1"}]


def test_from_api_response_treats_missing_scores_as_zero():
    course = Course.from_api_response(_api_payload(sweet=None, cold="", got=None, rate_count=None))
    assert (course.sweet, course.cold, course.got, course.rate_count) == (0.0, 0.0, 0.0, 0)


def test_from_api_response_rejects_payload_without_course_info():
    assert Course.from_api_response({}) is None
    assert Course.from_api_response(None) is None
    assert Course.from_api_response({"sweet": "9.0"}) is None


def test_to_dict_round_trips():
    course = Course(id="1", name="n", dept="d", teacher="t", sweet=1.5)
    assert Course(**course.to_dict()) == course


def test_add_field_chains_and_keeps_order():
    resp = BotResponse(title="t")
    assert resp.add_field("a", "1", inline=True).add_field("b", "2") is resp
    assert [(f.name, f.value, f.inline) for f in resp.fields] == [("a", "1", True), ("b", "2", False)]


def test_default_style_is_primary():
    assert BotResponse(title="t").style == ResponseStyle.PRIMARY


def test_to_markdown_layout():
    resp = BotResponse(title="Title", description="desc", footer="foot")
    resp.add_field("F1", "v1")
    resp.add_field("F2", "")  # empty value: only the field name is printed
    assert resp.to_markdown() == "**Title**\ndesc\n\n**F1**\nv1\n\n**F2**\n\n_foot_"


def test_to_markdown_skips_empty_parts():
    assert BotResponse(title="Only title").to_markdown() == "**Only title**"
    assert BotResponse(title="", description="d").to_markdown() == "d"
