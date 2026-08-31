#! python3
# clipsave - Save clipboard content to a timestamped file/copy in your
# Downloads folder. Auto-detects the type, no prompt needed:
#   - image                -> <timestamp>.png
#   - text                 -> <timestamp>.txt
#   - a copied file        -> <timestamp> <original name> (copied as-is)
#   - a copied folder      -> <timestamp> <folder name>.zip
#
# clipsave

import shutil
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageGrab

from core.stats import record_usage


def report_saved(action, path):
    print(f"{action}: {path.name}")
    print(f"Folder: {path.parent}")


def unique_path(path):
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def get_clipboard_text():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        return root.clipboard_get()
    except tk.TclError:
        return None
    finally:
        root.destroy()


def save_clipboard_files(paths, downloads, timestamp):
    saved_any = False
    for raw_path in paths:
        source = Path(raw_path)
        if not source.exists():
            print(f"Skipping '{source}': no longer exists.")
            continue

        if source.is_dir():
            target_zip = unique_path(downloads / f"{timestamp} {source.name}.zip")
            archive_base = target_zip.with_suffix("")
            archive_path = Path(
                shutil.make_archive(str(archive_base), "zip", root_dir=source.parent, base_dir=source.name)
            )
            report_saved("Zipped folder", archive_path)
        else:
            dest = unique_path(downloads / f"{timestamp} {source.name}")
            shutil.copy2(source, dest)
            report_saved("Copied file", dest)
        saved_any = True

    return saved_any


def main():
    record_usage("clipsave")
    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    clip_content = ImageGrab.grabclipboard()

    if isinstance(clip_content, Image.Image):
        path = unique_path(downloads / f"{timestamp}.png")
        clip_content.save(path)
        report_saved("Saved image", path)
        return

    if isinstance(clip_content, list) and clip_content:
        if save_clipboard_files(clip_content, downloads, timestamp):
            return

    text = get_clipboard_text()
    if text:
        path = unique_path(downloads / f"{timestamp}.txt")
        path.write_text(text, encoding="utf-8")
        report_saved("Saved text", path)
        return

    print("Clipboard is empty or contains unsupported content.")
    sys.exit(1)


if __name__ == "__main__":
    main()
