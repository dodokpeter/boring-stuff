# Generates the shared "B"-lettered Boring icon used by both the taskbar
# shortcut (setup_taskbar_icon.py) and the Explorer context menu
# (setup_explorer_menu.py) - one generated file, one place that draws it.

import os

from PIL import Image, ImageDraw, ImageFont


def generate_icon(icon_path):
    """Generate a 'B'-lettered .ico at icon_path (creating its parent
    directory if needed), with the multi-resolution sizes Windows expects
    for a shortcut/context-menu icon."""
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    font = None
    windir = os.environ.get("WINDIR")
    if windir:
        for name in ("arialbd.ttf", "segoeuib.ttf", "calibrib.ttf"):
            path = os.path.join(windir, "Fonts", name)
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
    img.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
