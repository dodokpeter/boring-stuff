from cases.webs import pinterest


def fake_response(xml_bytes):
    class FakeResponse:
        content = xml_bytes

        def raise_for_status(self):
            pass

    return FakeResponse()


def configure(monkeypatch, url="https://example.com/board.rss"):
    monkeypatch.setattr(
        pinterest, "load_config",
        lambda name: {"pinterest": {"randomBoard": url}},
    )


def test_opens_random_picture_link(monkeypatch):
    configure(monkeypatch)

    xml_response = b"""<rss><channel>
        <item><title>a</title><link>https://example.com/a.jpg</link></item>
        <item><title>b</title><link>https://example.com/b.jpg</link></item>
    </channel></rss>"""

    monkeypatch.setattr(pinterest.requests, "get", lambda url, fmt: fake_response(xml_response))
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

    monkeypatch.setattr(pinterest.requests, "get", lambda url, fmt: fake_response(xml_response))
    opened = []
    monkeypatch.setattr(pinterest.webbrowser, "open", lambda url: opened.append(url))

    pinterest.main()

    assert opened == ["https://example.com/only.jpg"]


def test_raises_when_board_not_configured(monkeypatch):
    monkeypatch.setattr(pinterest, "load_config", lambda name: {})

    try:
        pinterest.main()
        assert False, "expected a KeyError for missing config"
    except KeyError:
        pass
