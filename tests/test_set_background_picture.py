from pathlib import Path

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

    setBackgroundPicture.main()

    assert len(calls) == 1
    action, _param, path, _flags = calls[0]
    assert action == setBackgroundPicture.SPI_SETDESKWALLPAPER
    assert Path(path) == directory / "one.jpg"

    out = capsys.readouterr().out
    assert "one.jpg" in out


def test_raises_when_directory_not_configured(monkeypatch):
    monkeypatch.setattr(setBackgroundPicture, "load_config", lambda name: {})

    try:
        setBackgroundPicture.main()
        assert False, "expected a KeyError for missing config"
    except KeyError:
        pass
