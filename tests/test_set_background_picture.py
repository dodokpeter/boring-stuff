from pathlib import Path

import pytest

pytest.importorskip("winreg")

from cases.wins import setBackgroundPicture


def test_picks_a_random_wallpaper_and_applies_it(tmp_path, monkeypatch, capsys):
    directory = tmp_path / "wallpapers"
    directory.mkdir()
    (directory / "one.jpg").write_bytes(b"")
    (directory / "two.jpg").write_bytes(b"")

    monkeypatch.setattr(
        setBackgroundPicture, "load_config",
        lambda name: {"wallpaper": {"directory": str(directory)}},
    )
    monkeypatch.setattr(setBackgroundPicture.random, "choice", lambda seq: sorted(seq)[0])

    calls = []
    fake_spi = lambda *args: calls.append(args) or 1  # truthy = success, per Windows API
    monkeypatch.setattr(setBackgroundPicture, "get_sys_parameters_info", lambda: fake_spi)

    style_calls = []
    monkeypatch.setattr(setBackgroundPicture, "set_wallpaper_fit_style", lambda: style_calls.append(True))

    setBackgroundPicture.main()

    assert style_calls == [True]

    assert len(calls) == 1
    action, _param, path, _flags = calls[0]
    assert action == setBackgroundPicture.SPI_SETDESKWALLPAPER
    assert Path(path) == directory / "one.jpg"

    out = capsys.readouterr().out
    assert "one.jpg" in out


def test_set_wallpaper_fit_style_writes_fit_registry_values(monkeypatch):
    written = {}

    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    def fake_open_key(hive, subkey, reserved, access):
        assert subkey == r"Control Panel\Desktop"
        return FakeKey()

    def fake_set_value_ex(key, name, reserved, value_type, value):
        written[name] = value

    monkeypatch.setattr(setBackgroundPicture.winreg, "OpenKey", fake_open_key)
    monkeypatch.setattr(setBackgroundPicture.winreg, "SetValueEx", fake_set_value_ex)

    setBackgroundPicture.set_wallpaper_fit_style()

    assert written == {"WallpaperStyle": "6", "TileWallpaper": "0"}


def test_raises_when_directory_not_configured(monkeypatch):
    monkeypatch.setattr(setBackgroundPicture, "load_config", lambda name: {})

    try:
        setBackgroundPicture.main()
        assert False, "expected a KeyError for missing config"
    except KeyError:
        pass
