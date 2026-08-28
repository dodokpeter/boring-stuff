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
            archive_base = downloads / f"{timestamp} {source.name}"
            archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=source.parent, base_dir=source.name)
            print(f"Zipped folder to {archive_path}")
        else:
            dest = downloads / f"{timestamp} {source.name}"
            shutil.copy2(source, dest)
            print(f"Copied file to {dest}")
        saved_any = True

    return saved_any


def main():
    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    clip_content = ImageGrab.grabclipboard()

    if isinstance(clip_content, Image.Image):
        path = downloads / f"{timestamp}.png"
        clip_content.save(path)
        print(f"Saved image to {path}")
        return

    if isinstance(clip_content, list) and clip_content:
        if save_clipboard_files(clip_content, downloads, timestamp):
            return

    text = get_clipboard_text()
    if text:
        path = downloads / f"{timestamp}.txt"
        path.write_text(text, encoding="utf-8")
        print(f"Saved text to {path}")
        return

    print("Clipboard is empty or contains unsupported content.")
    sys.exit(1)


if __name__ == "__main__":
    main()
