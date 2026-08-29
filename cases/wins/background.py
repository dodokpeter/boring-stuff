#! python3
# Set the desktop background:
#   background          - a random picture from a configured directory
#   background <color>  - a solid color, matched against a standard palette
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml):
#   wallpaper:
#     directory: C:\Pictures\Wallpapers

import argparse
import ctypes
import os
import random
import struct
import winreg

from core.configuration.user_conf import load_config

SPI_SETDESKWALLPAPER = 20

# WallpaperStyle "6" = Fit: scale the image to fit inside the screen while
# keeping its aspect ratio, instead of the default stretch-to-fill.
WALLPAPER_STYLE_FIT = "6"
TILE_WALLPAPER_OFF = "0"

# Standard 12-color palette, as "R G B" values for the Control Panel\Colors
# "Background" registry value.
COLOR_PALETTE = {
    "red": "255 0 0",
    "orange": "255 165 0",
    "yellow": "255 255 0",
    "green": "0 128 0",
    "cyan": "0 255 255",
    "blue": "0 0 255",
    "purple": "128 0 128",
    "pink": "255 192 203",
    "brown": "165 42 42",
    "black": "0 0 0",
    "white": "255 255 255",
    "gray": "128 128 128",
}


def is_64_windows():
    """Find out how many bits is OS. """
    return struct.calcsize('P') * 8 == 64


def get_sys_parameters_info():
    """Based on if this is 32bit or 64bit returns correct version of SystemParametersInfo function. """
    return ctypes.windll.user32.SystemParametersInfoW if is_64_windows() \
        else ctypes.windll.user32.SystemParametersInfoA


def set_wallpaper_fit_style():
    """Set the desktop wallpaper style to "Fit" so a picture is scaled to fit
    the screen instead of being stretched. """
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, WALLPAPER_STYLE_FIT)
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, TILE_WALLPAPER_OFF)


def apply_wallpaper(path):
    sys_parameters_info = get_sys_parameters_info()
    result = sys_parameters_info(SPI_SETDESKWALLPAPER, 0, path, 3)

    # When the SPI_SETDESKWALLPAPER flag is used,
    # SystemParametersInfo returns TRUE
    # unless there is an error (like when the specified file doesn't exist).
    if not result:
        print(ctypes.WinError())


def set_solid_color_background(rgb):
    """Clear any wallpaper picture and set the desktop to a solid color. """
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Colors", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "Background", 0, winreg.REG_SZ, rgb)

    apply_wallpaper("")


def set_random_picture_background(directory):
    wallpaper_path = os.path.join(directory, random.choice(os.listdir(directory)))
    print(wallpaper_path)

    set_wallpaper_fit_style()
    apply_wallpaper(wallpaper_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set the desktop background")
    parser.add_argument(
        "color", nargs="?",
        help=f"solid color instead of a random picture, one of: {', '.join(sorted(COLOR_PALETTE))}",
    )
    args = parser.parse_args(argv)

    if args.color is not None:
        color = args.color.lower()
        rgb = COLOR_PALETTE.get(color)
        if rgb is None:
            parser.error(f"unknown color '{args.color}' - choose one of: {', '.join(sorted(COLOR_PALETTE))}")
        print(color)
        set_solid_color_background(rgb)
        return

    config = load_config(None)
    directory = config['wallpaper']['directory']
    set_random_picture_background(directory)


if __name__ == "__main__":
    main()
