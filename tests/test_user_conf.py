import pytest

from core.configuration import user_conf


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setattr(user_conf.Path, "home", lambda: tmp_path)
    return tmp_path


def test_create_config_path_creates_directory_and_stub_file(isolated_home):
    path = user_conf.create_config_path(None)

    assert path == isolated_home / ".boring-stuff" / "BoringStuff.yml"
    assert path.exists()
    assert "app: boring-stuff" in path.read_text(encoding="utf-8")


def test_create_config_path_with_named_config(isolated_home):
    path = user_conf.create_config_path("other.yml")

    assert path == isolated_home / ".boring-stuff" / "other.yml"
    assert path.exists()


def test_load_config_reads_existing_values():
    user_conf.save_config(None, {"me": {"name": "Ada"}})

    assert user_conf.load_config(None) == {"me": {"name": "Ada"}}


def test_load_config_returns_empty_dict_for_blank_file(isolated_home):
    config_dir = isolated_home / ".boring-stuff"
    config_dir.mkdir()
    (config_dir / "BoringStuff.yml").write_text("", encoding="utf-8")

    assert user_conf.load_config(None) == {}


def test_load_config_value_returns_existing_value_without_prompting(monkeypatch):
    user_conf.save_config(None, {"greeting": "hi"})

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should not prompt when value already exists")

    monkeypatch.setattr(user_conf, "ask_string_value", fail_if_called)

    assert user_conf.load_config_value(None, "Greeting?", "hello", "greeting") == "hi"


def test_load_config_value_prompts_and_persists_when_missing(monkeypatch):
    monkeypatch.setattr(user_conf, "ask_string_value", lambda message, default: "typed-value")

    result = user_conf.load_config_value(None, "Greeting?", "hello", "greeting")

    assert result == "typed-value"
    assert user_conf.load_config(None)["greeting"] == "typed-value"
