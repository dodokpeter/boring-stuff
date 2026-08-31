#! python3
# One-time setup for a "Boring" taskbar shortcut:
#   - generates a B-lettered icon
#   - creates Boring.lnk, whose default target runs clipsave
#   - registers a Jump List (right-click menu) with b64d/b64e/background/
#     json-pretty/json-pretty -m/email-extract tasks
#
# Run: uv run python cases/devs/taskbar/setup_taskbar_icon.py
# Then: open the folder it prints, right-click Boring.lnk, "Pin to taskbar".
# Safe to re-run any time to refresh the icon or the Jump List tasks.
#
# Run with --uninstall to remove the shortcut, icon, and Jump List again.

import argparse
import os
from pathlib import Path

import pythoncom
import win32com.propsys.propsys as propsys
import win32com.propsys.pscon as pscon
import win32com.shell.shell as shell
import win32com.shell.shellcon as shellcon
from PIL import Image, ImageDraw, ImageFont

APP_ID = "BoringStuff.Launcher"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TASKBAR_DIR = Path(__file__).resolve().parent
DATA_DIR = Path.home() / ".boring-stuff"
ICON_PATH = DATA_DIR / "boring.ico"
SHORTCUT_PATH = DATA_DIR / "Boring.lnk"
CMD_EXE = r"C:\Windows\System32\cmd.exe"

# (display title in the Jump List, .bat file to run, hover-tooltip command)
TASKS = [
    ("Decode base64 (b64d)", "run_b64d.bat", "b64d"),
    ("Encode base64 (b64e)", "run_b64e.bat", "b64e"),
    ("Set background", "run_background.bat", "background"),
    ("Pretty-print JSON", "run_json_pretty.bat", "json-pretty"),
    ("Minify JSON", "run_json_minify.bat", "json-pretty -m"),
    ("Extract email content", "run_email_extract.bat", "email-extract"),
]


def generate_icon():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    font = None
    for name in ("arialbd.ttf", "segoeuib.ttf", "calibrib.ttf"):
        path = os.path.join(os.environ["WINDIR"], "Fonts", name)
        if os.path.exists(path):
            font = ImageFont.truetype(path, 190)
            break
    if font is None:
        font = ImageFont.load_default()

    size = 256
    img = Image.new("RGBA", (size, size), (25, 25, 25, 255))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), "B", font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), "B", font=font, fill=(240, 200, 60, 255))
    img.save(ICON_PATH, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])


def make_link(bat_name, description=None):
    link = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLinkW
    )
    link.SetPath(CMD_EXE)
    link.SetArguments(f'/c "{TASKBAR_DIR / bat_name}"')
    link.SetIconLocation(str(ICON_PATH), 0)
    link.SetWorkingDirectory(str(REPO_ROOT))
    if description:
        # Shown as the hover tooltip in Explorer/the taskbar Jump List.
        link.SetDescription(description)
    return link


def set_title(link, title):
    store = link.QueryInterface(propsys.IID_IPropertyStore)
    store.SetValue(pscon.PKEY_Title, propsys.PROPVARIANTType(title))
    store.Commit()


def create_main_shortcut():
    link = make_link("run_clipsave.bat")
    link.SetDescription("Boring - clipsave")
    persist = link.QueryInterface(pythoncom.IID_IPersistFile)
    persist.Save(str(SHORTCUT_PATH), True)

    store = propsys.SHGetPropertyStoreFromParsingName(
        str(SHORTCUT_PATH), None, shellcon.GPS_READWRITE, propsys.IID_IPropertyStore
    )
    store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(APP_ID))
    store.Commit()


def make_task_collection(entries):
    collection = pythoncom.CoCreateInstance(
        shell.CLSID_EnumerableObjectCollection, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IObjectCollection
    )
    for title, bat_name, description in entries:
        task_link = make_link(bat_name, description=description)
        set_title(task_link, title)
        collection.AddObject(task_link)
    return collection.QueryInterface(shell.IID_IObjectArray)


def register_jump_list():
    dest_list = pythoncom.CoCreateInstance(
        shell.CLSID_DestinationList, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_ICustomDestinationList
    )
    dest_list.SetAppID(APP_ID)
    dest_list.BeginList()
    dest_list.AddUserTasks(make_task_collection(TASKS))
    dest_list.CommitList()


def uninstall():
    """Remove the registered Jump List, the pinned shortcut, and the
    generated icon. Deliberately does not touch BoringStuff.yml - removing
    someone's actual config (Pinterest board, wallpaper folder, etc.) is a
    separate decision, not a side effect of removing a taskbar shortcut.
    Windows has no supported API to un-pin a taskbar icon programmatically,
    so that step stays manual."""
    dest_list = pythoncom.CoCreateInstance(
        shell.CLSID_DestinationList, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_ICustomDestinationList
    )
    dest_list.DeleteList(APP_ID)

    for path in (SHORTCUT_PATH, ICON_PATH):
        path.unlink(missing_ok=True)

    print("Removed the Jump List registration, shortcut, and icon.")
    print("If it's still pinned, right-click it in the taskbar and choose 'Unpin from taskbar' to finish removing it.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set up (or remove) the Boring taskbar shortcut")
    parser.add_argument(
        "--uninstall", action="store_true", help="remove the shortcut, icon, and Jump List instead of installing them"
    )
    args = parser.parse_args(argv)

    if args.uninstall:
        uninstall()
        return

    generate_icon()
    create_main_shortcut()
    register_jump_list()

    print(f"Shortcut created: {SHORTCUT_PATH}")
    print("Right-click it in Explorer and choose 'Pin to taskbar' to finish setup.")
    print(
        "Left-click on the pinned icon runs clipsave; right-click shows the "
        "b64d/b64e/background/json-pretty/email-extract menu."
    )


if __name__ == "__main__":
    main()
