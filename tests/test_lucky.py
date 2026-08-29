import pytest

from cases.webs import lucky


def test_no_query_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        lucky.main([])
    assert exc_info.value.code == 2


def test_default_count_is_four(monkeypatch):
    seen = {}

    def fake_search(term, num_results):
        seen["term"] = term
        seen["num_results"] = num_results
        return ["https://example.com/a", "https://example.com/b"]

    monkeypatch.setattr(lucky, "search", fake_search)
    opened = []
    monkeypatch.setattr(lucky.webbrowser, "open", lambda url: opened.append(url))

    lucky.main(["tips", "for", "developers"])

    assert seen == {"term": "tips for developers", "num_results": 4}
    assert opened == ["https://example.com/a", "https://example.com/b"]


def test_n_flag_sets_result_count(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        lucky,
        "search",
        lambda term, num_results: seen.setdefault("num_results", num_results) or [],
    )
    monkeypatch.setattr(lucky.webbrowser, "open", lambda url: None)

    lucky.main(["-n3", "python", "requests"])

    assert seen["num_results"] == 3


def test_opens_each_scraped_result(monkeypatch):
    urls = ["https://a.example", "https://b.example", "https://c.example"]
    monkeypatch.setattr(lucky, "search", lambda term, num_results: urls)
    opened = []
    monkeypatch.setattr(lucky.webbrowser, "open", lambda url: opened.append(url))

    lucky.main(["some", "query"])

    assert opened == urls


def test_falls_back_to_search_page_when_no_results(monkeypatch):
    monkeypatch.setattr(lucky, "search", lambda term, num_results: [])
    opened = []
    monkeypatch.setattr(lucky.webbrowser, "open", lambda url: opened.append(url))

    lucky.main(["python", "requests", "library"])

    assert opened == ["https://www.google.com/search?q=python+requests+library"]


def test_falls_back_to_search_page_when_scraping_raises(monkeypatch):
    def raise_error(term, num_results):
        raise RuntimeError("blocked")

    monkeypatch.setattr(lucky, "search", raise_error)
    opened = []
    monkeypatch.setattr(lucky.webbrowser, "open", lambda url: opened.append(url))

    lucky.main(["weird & special?", "chars"])

    assert opened == ["https://www.google.com/search?q=weird+%26+special%3F+chars"]
