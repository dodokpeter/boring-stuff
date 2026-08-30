import pytest

from cases.webs import pinterest


def fake_response(xml_bytes):
    class FakeResponse:
        content = xml_bytes

        def raise_for_status(self):
            pass

    return FakeResponse()


def configure(monkeypatch, url="https://example.com/board.rss"):
    monkeypatch.setattr(pinterest, "load_config_value", lambda *args, **kwargs: url)


def test_opens_random_picture_link(monkeypatch):
    configure(monkeypatch)

    xml_response = b"""<rss><channel>
        <item><title>a</title><link>https://example.com/a.jpg</link></item>
        <item><title>b</title><link>https://example.com/b.jpg</link></item>
    </channel></rss>"""

    monkeypatch.setattr(pinterest.requests, "get", lambda url: fake_response(xml_response))
    monkeypatch.setattr(pinterest.random, "choice", lambda seq: seq[0])
    opened = []
    monkeypatch.setattr(pinterest.webbrowser, "open", lambda url: opened.append(url))

    pinterest.main()

    assert opened == ["https://example.com/a.jpg"]


def test_handles_a_feed_with_only_one_item(monkeypatch):
    # A single <item> parses as a plain dict rather than a list - make sure
    # that doesn't crash or get silently mishandled.
    configure(monkeypatch)

    xml_response = b"""<rss><channel>
        <item><title>only one</title><link>https://example.com/only.jpg</link></item>
    </channel></rss>"""

    monkeypatch.setattr(pinterest.requests, "get", lambda url: fake_response(xml_response))
    opened = []
    monkeypatch.setattr(pinterest.webbrowser, "open", lambda url: opened.append(url))

    pinterest.main()

    assert opened == ["https://example.com/only.jpg"]


def test_requests_get_is_called_with_only_the_url(monkeypatch):
    # Regression test: requests.get(url, "xml") used to pass "xml" as the
    # `params` argument, silently mangling the URL into "...?xml".
    configure(monkeypatch, url="https://example.com/board.rss")

    xml_response = b"<rss><channel><item><title>a</title><link>https://example.com/a.jpg</link></item></channel></rss>"
    captured = {}

    def fake_get(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return fake_response(xml_response)

    monkeypatch.setattr(pinterest.requests, "get", fake_get)
    monkeypatch.setattr(pinterest.webbrowser, "open", lambda url: None)

    pinterest.main()

    assert captured == {"args": ("https://example.com/board.rss",), "kwargs": {}}


def test_exits_cleanly_on_request_error(monkeypatch, capsys):
    configure(monkeypatch)

    def raise_http_error(url):
        raise pinterest.requests.exceptions.HTTPError("404 Client Error: Not Found")

    monkeypatch.setattr(pinterest.requests, "get", raise_http_error)

    with pytest.raises(SystemExit):
        pinterest.main()

    assert "Could not fetch" in capsys.readouterr().out


def test_exits_cleanly_on_malformed_xml(monkeypatch, capsys):
    configure(monkeypatch)

    monkeypatch.setattr(pinterest.requests, "get", lambda url: fake_response(b"not xml at all"))

    with pytest.raises(SystemExit):
        pinterest.main()

    assert "not valid XML" in capsys.readouterr().out


def test_prompts_and_persists_board_url_when_not_configured(monkeypatch):
    calls = []

    def fake_load_config_value(config_name, message, default, *keys, validate=None):
        calls.append((config_name, message, default, keys))
        return "https://example.com/board.rss"

    monkeypatch.setattr(pinterest, "load_config_value", fake_load_config_value)

    xml_response = b"""<rss><channel>
        <item><title>a</title><link>https://example.com/a.jpg</link></item>
    </channel></rss>"""
    monkeypatch.setattr(pinterest.requests, "get", lambda url: fake_response(xml_response))
    opened = []
    monkeypatch.setattr(pinterest.webbrowser, "open", lambda url: opened.append(url))

    pinterest.main()

    assert calls == [(None, "Pinterest board RSS URL", None, ("pinterest", "randomBoard"))]
    assert opened == ["https://example.com/a.jpg"]


def test_exits_cleanly_when_board_config_cannot_be_obtained(monkeypatch, capsys):
    def raise_missing(*args, **kwargs):
        raise pinterest.MissingConfigError("Pinterest board RSS URL is not configured, and no terminal is attached.")

    monkeypatch.setattr(pinterest, "load_config_value", raise_missing)

    with pytest.raises(SystemExit):
        pinterest.main()

    assert "not configured" in capsys.readouterr().out
