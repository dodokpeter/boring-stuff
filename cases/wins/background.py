#! python3
# Set the desktop background:
#   background          - a random picture from a configured directory
#   background <color>  - a solid color: first tried against a standard
#                          12-color palette, then against CSS3/X11 color
#                          names (e.g. "light blue", "steelblue")
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml):
#   wallpaper:
#     directory: C:\Pictures\Wallpapers

import argparse
import ctypes
import os
import random
import re
import struct
import sys
import winreg
from pathlib import Path

from PIL import Image, ImageColor

from core.configuration.user_conf import MissingConfigError, load_config_value

SPI_SETDESKWALLPAPER = 20

# WallpaperStyle: "6" = Fit (scale a picture to fit inside the screen,
# keeping its aspect ratio, instead of the default stretch-to-fill);
# "10" = Fill (scale to cover the screen, cropping if needed - used for
# solid colors, where cropping/scaling can't visibly distort anything).
WALLPAPER_STYLE_FIT = "6"
WALLPAPER_STYLE_FILL = "10"
TILE_WALLPAPER_OFF = "0"

# A solid color is applied as a generated image rather than through the
# legacy Control Panel\Colors registry key: modern Windows no longer honors
# that key for the actual desktop (SPI_SETDESKWALLPAPER with an empty path
# just shows black), so a real image is the only reliable way to get a flat
# color background.
BACKGROUND_COLOR_IMAGE = Path.home() / ".boring-stuff" / "background_color.bmp"

# Standard 12-color palette, as (R, G, B) tuples.
COLOR_PALETTE = {
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "green": (0, 128, 0),
    "cyan": (0, 255, 255),
    "blue": (0, 0, 255),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
}


def resolve_color(name):
    """Look up a color name's (R, G, B) tuple: first against the standard
    palette, then falling back to CSS3/X11 color names (spaces, dashes and
    underscores are stripped, so "light blue" matches "lightblue"). Returns
    None if neither matches."""
    normalized = name.strip().lower()
    if normalized in COLOR_PALETTE:
        return COLOR_PALETTE[normalized]

    css_name = re.sub(r"[\s_-]", "", normalized)
    try:
        return ImageColor.getrgb(css_name)
    except ValueError:
        return None


def is_64_windows():
    """Find out how many bits is OS."""
    return struct.calcsize("P") * 8 == 64


def get_sys_parameters_info():
    """Based on if this is 32bit or 64bit returns correct version of SystemParametersInfo function."""
    return ctypes.windll.user32.SystemParametersInfoW if is_64_windows() else ctypes.windll.user32.SystemParametersInfoA


def set_wallpaper_style(style):
    """Set the desktop WallpaperStyle in the registry (and disable tiling)."""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style)
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, TILE_WALLPAPER_OFF)


def set_wallpaper_fit_style():
    """Set the desktop wallpaper style to "Fit" so a picture is scaled to fit
    the screen instead of being stretched."""
    set_wallpaper_style(WALLPAPER_STYLE_FIT)


def apply_wallpaper(path):
    sys_parameters_info = get_sys_parameters_info()
    result = sys_parameters_info(SPI_SETDESKWALLPAPER, 0, path, 3)

    # When the SPI_SETDESKWALLPAPER flag is used,
    # SystemParametersInfo returns TRUE
    # unless there is an error (like when the specified file doesn't exist).
    if not result:
        print(ctypes.WinError())


def set_solid_color_background(rgb):
    """Generate a small solid-color image and apply it as the wallpaper."""
    BACKGROUND_COLOR_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32), rgb).save(BACKGROUND_COLOR_IMAGE, "BMP")

    set_wallpaper_style(WALLPAPER_STYLE_FILL)
    apply_wallpaper(str(BACKGROUND_COLOR_IMAGE))


def validate_wallpaper_directory(value):
    """Raise ValueError with a clear message if `value` isn't a usable
    wallpaper directory - used to reject a bad answer before it gets
    persisted to config (a typo'd or empty directory would otherwise only
    fail later, inside set_random_picture_background)."""
    directory = Path(value)
    if not directory.is_dir():
        raise ValueError(f"'{value}' is not a directory.")
    if not any(directory.iterdir()):
        raise ValueError(f"'{value}' is empty - add some pictures to it first.")


def set_random_picture_background(directory):
    wallpaper_path = os.path.join(directory, random.choice(os.listdir(directory)))
    print(wallpaper_path)

    set_wallpaper_fit_style()
    apply_wallpaper(wallpaper_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set the desktop background")
    parser.add_argument(
        "color",
        nargs="*",
        help=(
            "solid color instead of a random picture (e.g. 'green' or 'light blue'). "
            f"Tries the standard palette first ({', '.join(sorted(COLOR_PALETTE))}); "
            "if that doesn't match, falls back to CSS3/X11 color names."
        ),
    )
    args = parser.parse_args(argv)

    if args.color:
        color_input = " ".join(args.color)
        rgb = resolve_color(color_input)
        if rgb is None:
            parser.error(
                f"unknown color '{color_input}' - not in the standard palette "
                f"({', '.join(sorted(COLOR_PALETTE))}) or a CSS3/X11 color name"
            )
        print(color_input.lower())
        set_solid_color_background(rgb)
        return

    try:
        directory = load_config_value(
            None,
            "Wallpaper directory",
            None,
            "wallpaper",
            "directory",
            validate=validate_wallpaper_directory,
        )
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    set_random_picture_background(directory)


if __name__ == "__main__":
    main()
