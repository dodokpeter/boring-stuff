#! python3
# One-time setup for the "Boring" File Explorer right-click submenu:
#   - on files: move-to (share/output), negative, mp4to3, email-extract
#     (the last 3 only appear on their relevant extensions - see
#     FILE_ONLY_ITEMS_BY_EXTENSION below)
#   - on folders: move-to (share/output)
# Registered under HKCU (not HKLM/HKCR machine-wide), so no admin
# elevation is needed.
#
# Windows 11's redesigned context menu hides classic entries like these
# under "Show more options" (or Shift+right-click) by default - a known,
# accepted limitation (see issue #58), not a bug in this script.
#
# Run: uv run python cases/devs/explorer_menu/setup_explorer_menu.py
# Run with --uninstall to remove the registered menu again.

import argparse
import winreg
from pathlib import Path

MENU_DIR = Path(__file__).resolve().parent
REPO_ROOT = MENU_DIR.parent.parent.parent

SUBMENU_NAME = "Boring"
SUBMENU_LABEL = "Boring"

# Extensions "negative" shows up on - a reasonable common set, not
# exhaustive of everything Pillow can actually open (see issue #58).
NEGATIVE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]

# Shared by both the "*" (every file) and "Directory" (every folder)
# registrations - same two commands, same .bat wrappers either way.
MOVE_ITEMS = [
    ("MoveToShare", "Move to share", "run_move_to_share.bat"),
    ("MoveToOutput", "Move to output", "run_move_to_output.bat"),
]

# extension -> list of (subkey_name, label, bat_filename) - file-only
# items, scoped to where they're actually useful.
FILE_ONLY_ITEMS_BY_EXTENSION = {
    ".mp4": [("Mp4to3", "Extract mp3 (mp4to3)", "run_mp4to3.bat")],
    ".msg": [("EmailExtract", "Extract email (email-extract)", "run_email_extract_file.bat")],
    **{ext: [("Negative", "Invert to negative", "run_negative.bat")] for ext in NEGATIVE_EXTENSIONS},
}


def register_boring_submenu(class_key_path, items):
    """Create HKCU\\Software\\Classes\\<class_key_path>\\shell\\<SUBMENU_NAME>
    as a cascading submenu containing `items` - a list of
    (subkey_name, label, bat_filename) - each pointing at its .bat
    wrapper. MUIVerb + an empty SubCommands value is the standard registry
    mechanism for a cascading (as opposed to single-click) shell verb."""
    submenu_key_path = f"Software\\Classes\\{class_key_path}\\shell\\{SUBMENU_NAME}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, submenu_key_path) as submenu_key:
        winreg.SetValueEx(submenu_key, "MUIVerb", 0, winreg.REG_SZ, SUBMENU_LABEL)
        winreg.SetValueEx(submenu_key, "SubCommands", 0, winreg.REG_SZ, "")

    for subkey_name, label, bat_filename in items:
        item_key_path = f"{submenu_key_path}\\shell\\{subkey_name}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, item_key_path) as item_key:
            winreg.SetValueEx(item_key, "MUIVerb", 0, winreg.REG_SZ, label)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{item_key_path}\\command") as command_key:
            bat_path = MENU_DIR / bat_filename
            winreg.SetValueEx(command_key, None, 0, winreg.REG_SZ, f'"{bat_path}" "%1"')


def register_all():
    register_boring_submenu("*", MOVE_ITEMS)
    register_boring_submenu("Directory", MOVE_ITEMS)
    for extension, items in FILE_ONLY_ITEMS_BY_EXTENSION.items():
        register_boring_submenu(extension, items)


def delete_key_tree(root, path):
    """Recursively delete a registry key and everything under it - winreg
    has no built-in recursive delete. Safe to call on a key that doesn't
    exist (no-op)."""
    try:
        with winreg.OpenKey(root, path) as key:
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, 0)
                except OSError:
                    break
                delete_key_tree(root, f"{path}\\{subkey_name}")
        winreg.DeleteKey(root, path)
    except FileNotFoundError:
        pass


def uninstall():
    delete_key_tree(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\*\\shell\\{SUBMENU_NAME}")
    delete_key_tree(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\Directory\\shell\\{SUBMENU_NAME}")
    for extension in FILE_ONLY_ITEMS_BY_EXTENSION:
        delete_key_tree(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{extension}\\shell\\{SUBMENU_NAME}")
    print(f"Removed the '{SUBMENU_LABEL}' Explorer context menu.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set up (or remove) the 'Boring' Explorer right-click submenu")
    parser.add_argument("--uninstall", action="store_true", help="remove the registered menu instead of installing it")
    args = parser.parse_args(argv)

    if args.uninstall:
        uninstall()
        return

    register_all()
    print(f"Registered the '{SUBMENU_LABEL}' Explorer context menu (files and folders).")
    print("On Windows 11, look under 'Show more options' (or Shift+right-click) - see issue #58.")


if __name__ == "__main__":
    main()
