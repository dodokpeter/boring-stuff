#! python3
# Change desktop background picture to a random one from a configured
# directory.
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml):
#   wallpaper:
#     directory: C:\Pictures\Wallpapers

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


def is_64_windows():
    """Find out how many bits is OS. """
    return struct.calcsize('P') * 8 == 64


def get_sys_parameters_info():
    """Based on if this is 32bit or 64bit returns correct version of SystemParametersInfo function. """
    return ctypes.windll.user32.SystemParametersInfoW if is_64_windows() \
        else ctypes.windll.user32.SystemParametersInfoA


def set_wallpaper_fit_style():
    """Set the desktop wallpaper style to "Fit" so the picture is scaled to fit
    the screen instead of being stretched. """
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, WALLPAPER_STYLE_FIT)
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, TILE_WALLPAPER_OFF)


def main():
    config = load_config(None)
    directory = config['wallpaper']['directory']

    wallpaper_path = os.path.join(directory, random.choice(os.listdir(directory)))
    print(wallpaper_path)

    set_wallpaper_fit_style()

    sys_parameters_info = get_sys_parameters_info()
    result = sys_parameters_info(SPI_SETDESKWALLPAPER, 0, wallpaper_path, 3)

    # When the SPI_SETDESKWALLPAPER flag is used,
    # SystemParametersInfo returns TRUE
    # unless there is an error (like when the specified file doesn't exist).
    if not result:
        print(ctypes.WinError())


if __name__ == "__main__":
    main()
