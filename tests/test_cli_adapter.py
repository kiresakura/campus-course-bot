"""Terminal adapter tests: command routing, rendering and the input loop (no network).

Chinese strings below are test data / production UI strings the code returns."""

import asyncio
import io

import run
from adapters.cli_adapter import HELP_TEXT, CliAdapter


def _reply(adapter, line):
    return asyncio.run(adapter.reply(line))


def test_render_is_the_neutral_markdown(service):
    resp = service.search("微積分")
    assert CliAdapter(service).render(resp) == resp.to_markdown()


def test_english_alias_chinese_name_and_slash_route_the_same(service):
    a = CliAdapter(service)
    expected = a.render(service.search("微積分"))
    assert _reply(a, "search 微積分") == expected
    assert _reply(a, "SEARCH 微積分") == expected
    assert _reply(a, "課程 微積分") == expected
    assert _reply(a, "/search 微積分") == expected


def test_commands_reach_the_service(service):
    a = CliAdapter(service)
    assert _reply(a, "professor 王小明") == a.render(service.professor("王小明"))
    assert _reply(a, "sweet") == a.render(service.top_sweet())
    assert _reply(a, "cold 外語") == a.render(service.top_cold("外語"))
    assert _reply(a, "compare 微積分 大學英文") == a.render(service.compare("微積分", "大學英文"))
    assert _reply(a, "worst 2") == a.render(service.worst(2))
    assert _reply(a, "worst abc") == a.render(service.worst(5))  # non-numeric: default


def test_detail_awaits_the_service(service, monkeypatch):
    async def fake_fetch(*args, **kwargs):
        return None

    monkeypatch.setattr(service.client, "fetch_course", fake_fetch)
    assert "課程 ID 42 不存在" in _reply(CliAdapter(service), "詳細 42")


def test_unknown_or_incomplete_input_shows_help(service):
    a = CliAdapter(service)
    for line in ("", "help", "hello", "search", "compare 微積分", "detail abc"):
        assert _reply(a, line) == HELP_TEXT


def test_loop_answers_until_quit(service, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("search 微積分\n\nquit\nsweet\n"))
    CliAdapter(service).start()
    out = capsys.readouterr().out
    assert out.count("搜尋結果：微積分") == 1
    assert "甜度排行榜" not in out  # input after "quit" is never read


def test_loop_stops_at_end_of_input(service, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("sweet\n"))
    CliAdapter(service).start()  # returns instead of raising EOFError
    assert "甜度排行榜" in capsys.readouterr().out


def test_run_builds_the_cli_adapter(service):
    assert isinstance(run.build_adapter("cli", service), CliAdapter)


def test_run_rejects_unknown_platform_without_traceback(capsys):
    assert run.main(["--platform", "nope"]) == 1
    err = capsys.readouterr().err
    assert "Unknown platform 'nope'" in err
    assert "Traceback" not in err
