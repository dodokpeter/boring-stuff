from cases.webs import openwebs


def test_no_args_opens_all_default_groups(monkeypatch):
    opened = []
    monkeypatch.setattr(openwebs, "load_config", lambda name: {})
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))

    openwebs.main([])

    assert len(opened) == 3 + 5 + 3
    assert "https://mail.google.com" in opened
    assert "https://facebook.com" in opened
    assert "https://hnonline.sk" in opened


def test_specific_group_only(monkeypatch):
    opened = []
    monkeypatch.setattr(openwebs, "load_config", lambda name: {})
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))

    openwebs.main(["init"])

    assert opened == [
        "https://mail.google.com",
        "https://calendar.google.com",
        "https://translate.google.com",
    ]


def test_multiple_tags_open_each_group(monkeypatch):
    opened = []
    monkeypatch.setattr(openwebs, "load_config", lambda name: {})
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))

    openwebs.main(["s", "n"])

    assert len(opened) == 5 + 3
    assert "https://facebook.com" in opened
    assert "https://hnonline.sk" in opened


def test_user_config_fully_replaces_default_groups(monkeypatch):
    opened = []
    monkeypatch.setattr(
        openwebs, "load_config",
        lambda name: {"openwebs": {"work": ["https://example.com/inbox", "https://example.com/tickets"]}},
    )
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))

    openwebs.main(["work"])

    assert opened == ["https://example.com/inbox", "https://example.com/tickets"]


def test_unknown_tag_opens_nothing(monkeypatch):
    opened = []
    monkeypatch.setattr(openwebs, "load_config", lambda name: {})
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))

    openwebs.main(["nope"])

    assert opened == []
