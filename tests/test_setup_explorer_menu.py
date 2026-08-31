import pytest

pytest.importorskip("winreg")

import winreg

from cases.devs.explorer_menu import setup_explorer_menu


@pytest.fixture(autouse=True)
def isolated_submenu_name(monkeypatch):
    # Never touch the real "Boring" submenu - that's the one that would
    # show up in the developer's actual right-click menu.
    monkeypatch.setattr(setup_explorer_menu, "SUBMENU_NAME", "BoringTest")
    yield
    setup_explorer_menu.uninstall()


def read_default_value(path):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        value, _type = winreg.QueryValueEx(key, None)
        return value


def read_named_value(path, name):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        value, _type = winreg.QueryValueEx(key, name)
        return value


def key_exists(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path):
            return True
    except FileNotFoundError:
        return False


def test_register_boring_submenu_creates_muiverb_and_subcommands(tmp_path):
    setup_explorer_menu.register_boring_submenu("BoringTestClass", [("Item", "Do the thing", "run_x.bat")])

    base = "Software\\Classes\\BoringTestClass\\shell\\BoringTest"
    assert read_named_value(base, "MUIVerb") == setup_explorer_menu.SUBMENU_LABEL
    assert read_named_value(base, "SubCommands") == ""

    setup_explorer_menu.delete_key_tree(winreg.HKEY_CURRENT_USER, "Software\\Classes\\BoringTestClass")


def test_register_boring_submenu_creates_item_and_command(tmp_path):
    setup_explorer_menu.register_boring_submenu("BoringTestClass2", [("Item", "Do the thing", "run_x.bat")])

    item_base = "Software\\Classes\\BoringTestClass2\\shell\\BoringTest\\shell\\Item"
    assert read_named_value(item_base, "MUIVerb") == "Do the thing"

    command = read_default_value(f"{item_base}\\command")
    expected_bat = setup_explorer_menu.MENU_DIR / "run_x.bat"
    assert command == f'"{expected_bat}" "%1"'

    setup_explorer_menu.delete_key_tree(winreg.HKEY_CURRENT_USER, "Software\\Classes\\BoringTestClass2")


def test_register_boring_submenu_creates_multiple_items(tmp_path):
    setup_explorer_menu.register_boring_submenu(
        "BoringTestClass3",
        [("First", "First item", "run_a.bat"), ("Second", "Second item", "run_b.bat")],
    )

    first_item = "Software\\Classes\\BoringTestClass3\\shell\\BoringTest\\shell\\First"
    second_item = "Software\\Classes\\BoringTestClass3\\shell\\BoringTest\\shell\\Second"
    assert read_named_value(first_item, "MUIVerb") == "First item"
    assert read_named_value(second_item, "MUIVerb") == "Second item"

    setup_explorer_menu.delete_key_tree(winreg.HKEY_CURRENT_USER, "Software\\Classes\\BoringTestClass3")


def test_register_all_covers_star_directory_and_every_extension():
    setup_explorer_menu.register_all()

    assert key_exists("Software\\Classes\\*\\shell\\BoringTest")
    assert key_exists("Software\\Classes\\Directory\\shell\\BoringTest")
    for extension in setup_explorer_menu.FILE_ONLY_ITEMS_BY_EXTENSION:
        assert key_exists(f"Software\\Classes\\{extension}\\shell\\BoringTest")


def test_register_all_puts_both_move_items_on_files_and_folders():
    setup_explorer_menu.register_all()

    for class_key in ("*", "Directory"):
        assert key_exists(f"Software\\Classes\\{class_key}\\shell\\BoringTest\\shell\\MoveToShare")
        assert key_exists(f"Software\\Classes\\{class_key}\\shell\\BoringTest\\shell\\MoveToOutput")


def test_uninstall_removes_everything_register_all_created():
    setup_explorer_menu.register_all()

    setup_explorer_menu.uninstall()

    assert not key_exists("Software\\Classes\\*\\shell\\BoringTest")
    assert not key_exists("Software\\Classes\\Directory\\shell\\BoringTest")
    for extension in setup_explorer_menu.FILE_ONLY_ITEMS_BY_EXTENSION:
        assert not key_exists(f"Software\\Classes\\{extension}\\shell\\BoringTest")


def test_uninstall_runs_without_error_when_nothing_was_installed():
    setup_explorer_menu.uninstall()  # must not raise


def test_delete_key_tree_removes_nested_keys():
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Classes\\BoringTestTree\\a\\b\\c").Close()

    setup_explorer_menu.delete_key_tree(winreg.HKEY_CURRENT_USER, "Software\\Classes\\BoringTestTree")

    assert not key_exists("Software\\Classes\\BoringTestTree")


def test_delete_key_tree_is_a_noop_for_a_missing_key():
    path = "Software\\Classes\\BoringTestDoesNotExist"
    setup_explorer_menu.delete_key_tree(winreg.HKEY_CURRENT_USER, path)  # must not raise


def test_main_uninstall_flag_calls_uninstall(monkeypatch):
    called = []
    monkeypatch.setattr(setup_explorer_menu, "uninstall", lambda: called.append(True))

    setup_explorer_menu.main(["--uninstall"])

    assert called == [True]


def test_main_installs_by_default(monkeypatch):
    called = []
    monkeypatch.setattr(setup_explorer_menu, "register_all", lambda: called.append(True))

    setup_explorer_menu.main([])

    assert called == [True]
