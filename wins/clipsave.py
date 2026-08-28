#! python3
# clipsave - Save clipboard content (image or text) to a timestamped file
# in your Downloads folder. Auto-detects the type, no prompt needed.
#
# clipsave

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


def main():
    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    image = ImageGrab.grabclipboard()
    if isinstance(image, Image.Image):
        path = downloads / f"{timestamp}.png"
        image.save(path)
        print(f"Saved image to {path}")
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
