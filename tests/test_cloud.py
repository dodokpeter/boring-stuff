import pytest

from core import cloud


def test_validate_cloud_folder_rejects_missing_path(tmp_path):
    with pytest.raises(ValueError):
        cloud.validate_cloud_folder(str(tmp_path / "nope"))


def test_validate_cloud_folder_accepts_existing_directory(tmp_path):
    cloud.validate_cloud_folder(str(tmp_path))  # does not raise


def test_load_cloud_folder_prompts_with_expected_message_and_no_default(tmp_path, monkeypatch):
    calls = []

    def fake_load_config_value(config_name, message, default, *keys, validate=None):
        calls.append((config_name, message, default, keys))
        if validate is not None:
            validate(str(tmp_path))
        return str(tmp_path)

    monkeypatch.setattr(cloud, "load_config_value", fake_load_config_value)

    result = cloud.load_cloud_folder()

    assert result == tmp_path
    assert calls == [(None, "Cloud folder root (e.g. your Google Drive mount path)", None, ("cloud", "folder"))]


def test_load_cloud_subfolder_name_prompts_with_key_and_default(monkeypatch):
    calls = []

    def fake_load_config_value(config_name, message, default, *keys, validate=None):
        calls.append((config_name, message, default, keys))
        return default

    monkeypatch.setattr(cloud, "load_config_value", fake_load_config_value)

    result = cloud.load_cloud_subfolder_name("output", "output")

    assert result == "output"
    assert calls == [(None, "Cloud 'output' subfolder name", "output", ("cloud", "output"))]
