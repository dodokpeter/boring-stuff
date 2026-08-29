from cases.webs import pinterest


def test_opens_random_picture_link(tmp_path, monkeypatch):
    ini = tmp_path / "BoringStuff.ini"
    ini.write_text(
        "[Pinterest]\nRandomBoard: https://example.com/board.rss\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(pinterest.Path, "home", lambda: tmp_path)

    # Two <item> entries so xmltodict parses a list (a single <item> would
    # parse as a plain dict instead, which the script doesn't handle).
    xml_response = b"""<rss><channel>
        <item><title>a</title><link>https://example.com/a.jpg</link></item>
        <item><title>b</title><link>https://example.com/b.jpg</link></item>
    </channel></rss>"""

    class FakeResponse:
        content = xml_response

        def raise_for_status(self):
            pass

    monkeypatch.setattr(pinterest.requests, "get", lambda url, fmt: FakeResponse())
    monkeypatch.setattr(pinterest.random, "randint", lambda a, b: 0)
    opened = []
    monkeypatch.setattr(pinterest.webbrowser, "open", lambda url: opened.append(url))

    pinterest.main()

    assert opened == ["https://example.com/a.jpg"]
