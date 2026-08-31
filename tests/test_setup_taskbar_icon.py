import pytest

pytest.importorskip("win32com.shell.shell")

from PIL import Image

from cases.devs.taskbar import setup_taskbar_icon


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    data_dir = tmp_path / ".boring-stuff"
    monkeypatch.setattr(setup_taskbar_icon, "DATA_DIR", data_dir)
    monkeypatch.setattr(setup_taskbar_icon, "ICON_PATH", data_dir / "boring.ico")
    monkeypatch.setattr(setup_taskbar_icon, "SHORTCUT_PATH", data_dir / "Boring.lnk")
    # Never touch the real "BoringStuff.Launcher" app id - that's the one
    # registered against the user's actual pinned taskbar icon.
    monkeypatch.setattr(setup_taskbar_icon, "APP_ID", "BoringStuff.Test")
    return data_dir


def test_generate_icon_creates_multi_size_ico():
    setup_taskbar_icon.generate_icon()

    icon_path = setup_taskbar_icon.ICON_PATH
    assert icon_path.exists()
    with Image.open(icon_path) as img:
        assert set(img.info.get("sizes", [])) >= {(16, 16), (32, 32), (48, 48), (256, 256)}


def test_make_link_targets_cmd_with_the_right_bat_and_workdir():
    setup_taskbar_icon.generate_icon()
    link = setup_taskbar_icon.make_link("run_b64d.bat")

    path, _find_data = link.GetPath(0)
    assert path.lower() == setup_taskbar_icon.CMD_EXE.lower()
    assert "run_b64d.bat" in link.GetArguments()
    assert link.GetWorkingDirectory() == str(setup_taskbar_icon.REPO_ROOT)


def test_make_link_sets_description_as_hover_tooltip():
    setup_taskbar_icon.generate_icon()
    link = setup_taskbar_icon.make_link("run_background.bat", description="background")

    assert link.GetDescription() == "background"


def test_tasks_includes_email_extract():
    bat_names = [bat_name for _title, bat_name, _description in setup_taskbar_icon.TASKS]
    assert "run_email_extract.bat" in bat_names


def test_make_task_collection_builds_one_link_per_entry():
    # IObjectArray.GetAt(index, IID) segfaults in this pywin32 environment
    # (reproduced outside pytest too), so - like register_jump_list below -
    # this only checks what can safely be introspected: the item count.
    # Each entry's link content (path/args/description/title) is covered by
    # make_link's and set_title's own tests above.
    setup_taskbar_icon.generate_icon()
    array = setup_taskbar_icon.make_task_collection(
        [
            ("Pretty-print", "run_json_pretty.bat", "json-pretty"),
            ("Minify", "run_json_minify.bat", "json-pretty -m"),
        ]
    )

    assert array.GetCount() == 2


def test_create_main_shortcut_writes_lnk_with_app_id():
    import win32com.propsys.propsys as propsys
    import win32com.propsys.pscon as pscon
    import win32com.shell.shellcon as shellcon

    setup_taskbar_icon.generate_icon()
    setup_taskbar_icon.create_main_shortcut()

    shortcut_path = setup_taskbar_icon.SHORTCUT_PATH
    assert shortcut_path.exists()

    store = propsys.SHGetPropertyStoreFromParsingName(
        str(shortcut_path), None, shellcon.GPS_DEFAULT, propsys.IID_IPropertyStore
    )
    app_id = store.GetValue(pscon.PKEY_AppUserModel_ID).GetValue()
    assert app_id == "BoringStuff.Test"


def test_register_jump_list_runs_without_error():
    # Exercises the real ICustomDestinationList COM calls, isolated under
    # the "BoringStuff.Test" app id from the fixture above - this cannot
    # affect the real pinned icon's Jump List. There's no supported way to
    # read a Jump List's registered tasks back via COM to assert against,
    # so this is a smoke test: it passes if no COM error is raised.
    setup_taskbar_icon.generate_icon()
    setup_taskbar_icon.create_main_shortcut()

    setup_taskbar_icon.register_jump_list()


def test_uninstall_removes_shortcut_and_icon_files():
    setup_taskbar_icon.generate_icon()
    setup_taskbar_icon.create_main_shortcut()
    assert setup_taskbar_icon.ICON_PATH.exists()
    assert setup_taskbar_icon.SHORTCUT_PATH.exists()

    setup_taskbar_icon.uninstall()

    assert not setup_taskbar_icon.ICON_PATH.exists()
    assert not setup_taskbar_icon.SHORTCUT_PATH.exists()


def test_uninstall_does_not_touch_boringstuff_yml(isolated_paths):
    isolated_paths.mkdir(parents=True, exist_ok=True)
    config_file = isolated_paths / "BoringStuff.yml"
    config_file.write_text("app: boring-stuff\n", encoding="utf-8")

    setup_taskbar_icon.generate_icon()
    setup_taskbar_icon.create_main_shortcut()

    setup_taskbar_icon.uninstall()

    assert config_file.exists()


def test_uninstall_runs_without_error_when_nothing_was_installed():
    # Safe to call even if setup was never run - no files to delete, and
    # DeleteList on an app id with no registered Jump List is a no-op.
    setup_taskbar_icon.uninstall()


def test_main_uninstall_flag_calls_uninstall(monkeypatch):
    called = []
    monkeypatch.setattr(setup_taskbar_icon, "uninstall", lambda: called.append(True))

    setup_taskbar_icon.main(["--uninstall"])

    assert called == [True]
