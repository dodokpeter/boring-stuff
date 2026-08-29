from cases.webs import openwebs


def test_no_args_opens_all_three_groups(monkeypatch):
    opened = []
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(openwebs.sys, "argv", ["openwebs"])

    openwebs.main()

    assert len(opened) == 3 + 5 + 3
    assert "https://mail.google.com" in opened
    assert "https://facebook.com" in opened
    assert "https://hnonline.sk" in opened


def test_specific_group_only(monkeypatch):
    opened = []
    monkeypatch.setattr(openwebs.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(openwebs.sys, "argv", ["openwebs", "init"])

    openwebs.main()

    assert opened == [
        "https://mail.google.com",
        "https://calendar.google.com",
        "https://translate.google.com",
    ]
