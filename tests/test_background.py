from pathlib import Path

import pytest

pytest.importorskip("winreg")

from PIL import Image

from cases.wins import background


class FakeKey:
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.fixture
def fake_registry(monkeypatch):
    """Replace winreg.OpenKey/SetValueEx with in-memory stand-ins and return
    the dict that SetValueEx calls get recorded into."""
    written = {}
    monkeypatch.setattr(background.winreg, "OpenKey", lambda *a, **k: FakeKey())
    monkeypatch.setattr(
        background.winreg,
        "SetValueEx",
        lambda key, name, reserved, value_type, value: written.__setitem__(name, value),
    )
    return written


@pytest.fixture
def fake_spi(monkeypatch):
    """Replace get_sys_parameters_info with a stand-in that records calls
    and always reports success."""
    calls = []
    monkeypatch.setattr(background, "get_sys_parameters_info", lambda: lambda *args: calls.append(args) or 1)
    return calls


def test_picks_a_random_wallpaper_and_applies_it(tmp_path, monkeypatch, fake_spi, capsys):
    directory = tmp_path / "wallpapers"
    directory.mkdir()
    (directory / "one.jpg").write_bytes(b"")
    (directory / "two.jpg").write_bytes(b"")

    monkeypatch.setattr(background, "load_config_value", lambda *args, **kwargs: str(directory))
    monkeypatch.setattr(background.random, "choice", lambda seq: sorted(seq)[0])

    style_calls = []
    monkeypatch.setattr(background, "set_wallpaper_fit_style", lambda: style_calls.append(True))

    background.main([])

    assert style_calls == [True]

    assert len(fake_spi) == 1
    action, _param, path, _flags = fake_spi[0]
    assert action == background.SPI_SETDESKWALLPAPER
    assert Path(path) == directory / "one.jpg"

    out = capsys.readouterr().out
    assert "one.jpg" in out


def test_set_wallpaper_fit_style_writes_fit_registry_values(fake_registry):
    background.set_wallpaper_fit_style()

    assert fake_registry == {"WallpaperStyle": "6", "TileWallpaper": "0"}


def test_prompts_and_persists_directory_when_not_configured(tmp_path, monkeypatch, fake_spi):
    directory = tmp_path / "wallpapers"
    directory.mkdir()
    (directory / "one.jpg").write_bytes(b"")
    monkeypatch.setattr(background.random, "choice", lambda seq: sorted(seq)[0])

    calls = []

    def fake_load_config_value(config_name, message, default, *keys, validate=None):
        calls.append((config_name, message, default, keys))
        if validate is not None:
            validate(str(directory))
        return str(directory)

    monkeypatch.setattr(background, "load_config_value", fake_load_config_value)

    background.main([])

    assert calls == [(None, "Wallpaper directory", None, ("wallpaper", "directory"))]

    assert len(fake_spi) == 1
    action, _param, path, _flags = fake_spi[0]
    assert action == background.SPI_SETDESKWALLPAPER
    assert Path(path) == directory / "one.jpg"


def test_exits_cleanly_when_config_cannot_be_obtained(monkeypatch, capsys):
    def raise_missing(*args, **kwargs):
        raise background.MissingConfigError("Wallpaper directory is not configured, and no terminal is attached.")

    monkeypatch.setattr(background, "load_config_value", raise_missing)

    with pytest.raises(SystemExit):
        background.main([])

    assert "not configured" in capsys.readouterr().out


def test_validate_wallpaper_directory_rejects_missing_path(tmp_path):
    with pytest.raises(ValueError):
        background.validate_wallpaper_directory(str(tmp_path / "nope"))


def test_validate_wallpaper_directory_rejects_empty_directory(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError):
        background.validate_wallpaper_directory(str(empty_dir))


def test_validate_wallpaper_directory_accepts_directory_with_a_file(tmp_path):
    ok_dir = tmp_path / "ok"
    ok_dir.mkdir()
    (ok_dir / "pic.jpg").write_bytes(b"")

    background.validate_wallpaper_directory(str(ok_dir))  # does not raise


def test_color_argument_generates_solid_color_image_and_applies_it(
    tmp_path,
    monkeypatch,
    fake_registry,
    fake_spi,
    capsys,
):
    image_path = tmp_path / "background_color.bmp"
    monkeypatch.setattr(background, "BACKGROUND_COLOR_IMAGE", image_path)

    background.main(["green"])

    assert image_path.exists()
    with Image.open(image_path) as img:
        assert img.convert("RGB").getpixel((0, 0)) == (0, 128, 0)

    assert fake_registry == {"WallpaperStyle": "10", "TileWallpaper": "0"}

    assert len(fake_spi) == 1
    action, _param, path, _flags = fake_spi[0]
    assert action == background.SPI_SETDESKWALLPAPER
    assert path == str(image_path)

    out = capsys.readouterr().out
    assert "green" in out


def test_color_argument_is_case_insensitive(tmp_path, monkeypatch, fake_registry, fake_spi):
    image_path = tmp_path / "background_color.bmp"
    monkeypatch.setattr(background, "BACKGROUND_COLOR_IMAGE", image_path)

    background.main(["GrEeN"])

    with Image.open(image_path) as img:
        assert img.convert("RGB").getpixel((0, 0)) == (0, 128, 0)


def test_unknown_color_exits_with_error(capsys):
    with pytest.raises(SystemExit):
        background.main(["not-a-real-color"])

    err = capsys.readouterr().err
    assert "unknown color" in err


def test_resolve_color_prefers_the_standard_palette():
    assert background.resolve_color("green") == (0, 128, 0)


def test_resolve_color_falls_back_to_css3_x11_names():
    assert background.resolve_color("light blue") == (173, 216, 230)
    assert background.resolve_color("steelblue") == (70, 130, 180)


def test_resolve_color_returns_none_for_unknown_name():
    assert background.resolve_color("not-a-real-color") is None


def test_multi_word_color_argument_resolves_via_css3_x11(tmp_path, monkeypatch, fake_registry, fake_spi, capsys):
    image_path = tmp_path / "background_color.bmp"
    monkeypatch.setattr(background, "BACKGROUND_COLOR_IMAGE", image_path)

    background.main(["light", "blue"])

    with Image.open(image_path) as img:
        assert img.convert("RGB").getpixel((0, 0)) == (173, 216, 230)

    assert "light blue" in capsys.readouterr().out
