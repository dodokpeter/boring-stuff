from pathlib import Path

import pytest

pytest.importorskip("winreg")

from cases.wins import background


class FakeKey:
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.fixture
def fake_registry(monkeypatch):
    """Replace winreg.OpenKey/SetValueEx with in-memory stand-ins and return
    the dict that SetValueEx calls get recorded into. """
    written = {}
    monkeypatch.setattr(background.winreg, "OpenKey", lambda *a, **k: FakeKey())
    monkeypatch.setattr(
        background.winreg, "SetValueEx",
        lambda key, name, reserved, value_type, value: written.__setitem__(name, value),
    )
    return written


def test_picks_a_random_wallpaper_and_applies_it(tmp_path, monkeypatch, capsys):
    directory = tmp_path / "wallpapers"
    directory.mkdir()
    (directory / "one.jpg").write_bytes(b"")
    (directory / "two.jpg").write_bytes(b"")

    monkeypatch.setattr(
        background, "load_config",
        lambda name: {"wallpaper": {"directory": str(directory)}},
    )
    monkeypatch.setattr(background.random, "choice", lambda seq: sorted(seq)[0])

    calls = []
    fake_spi = lambda *args: calls.append(args) or 1  # truthy = success, per Windows API
    monkeypatch.setattr(background, "get_sys_parameters_info", lambda: fake_spi)

    style_calls = []
    monkeypatch.setattr(background, "set_wallpaper_fit_style", lambda: style_calls.append(True))

    background.main([])

    assert style_calls == [True]

    assert len(calls) == 1
    action, _param, path, _flags = calls[0]
    assert action == background.SPI_SETDESKWALLPAPER
    assert Path(path) == directory / "one.jpg"

    out = capsys.readouterr().out
    assert "one.jpg" in out


def test_set_wallpaper_fit_style_writes_fit_registry_values(fake_registry):
    background.set_wallpaper_fit_style()

    assert fake_registry == {"WallpaperStyle": "6", "TileWallpaper": "0"}


def test_raises_when_directory_not_configured(monkeypatch):
    monkeypatch.setattr(background, "load_config", lambda name: {})

    try:
        background.main([])
        assert False, "expected a KeyError for missing config"
    except KeyError:
        pass


def test_color_argument_sets_solid_background(fake_registry, monkeypatch, capsys):
    calls = []
    fake_spi = lambda *args: calls.append(args) or 1
    monkeypatch.setattr(background, "get_sys_parameters_info", lambda: fake_spi)

    background.main(["green"])

    assert fake_registry == {"Background": "0 128 0"}

    assert len(calls) == 1
    action, _param, path, _flags = calls[0]
    assert action == background.SPI_SETDESKWALLPAPER
    assert path == ""

    out = capsys.readouterr().out
    assert "green" in out


def test_color_argument_is_case_insensitive(fake_registry, monkeypatch):
    monkeypatch.setattr(background, "get_sys_parameters_info", lambda: (lambda *args: 1))

    background.main(["GrEeN"])

    assert fake_registry == {"Background": "0 128 0"}


def test_unknown_color_exits_with_error(capsys):
    with pytest.raises(SystemExit):
        background.main(["not-a-real-color"])

    err = capsys.readouterr().err
    assert "unknown color" in err


def test_resolve_color_prefers_the_standard_palette():
    assert background.resolve_color("green") == "0 128 0"


def test_resolve_color_falls_back_to_css3_x11_names():
    assert background.resolve_color("light blue") == "173 216 230"
    assert background.resolve_color("steelblue") == "70 130 180"


def test_resolve_color_returns_none_for_unknown_name():
    assert background.resolve_color("not-a-real-color") is None


def test_multi_word_color_argument_resolves_via_css3_x11(fake_registry, monkeypatch, capsys):
    monkeypatch.setattr(background, "get_sys_parameters_info", lambda: (lambda *args: 1))

    background.main(["light", "blue"])

    assert fake_registry == {"Background": "173 216 230"}
    assert "light blue" in capsys.readouterr().out
