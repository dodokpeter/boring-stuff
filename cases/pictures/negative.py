#! python3
# negative - invert every picture in a folder to its negative, saved into a
# "negative" subfolder alongside the originals (so a second run doesn't
# invert its own output).
#
# negative <folder>

import argparse
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from core.stats import record_usage


def main(argv=None):
    record_usage("negative")
    parser = argparse.ArgumentParser(description="Invert every picture in a folder to its negative")
    parser.add_argument("directory", nargs="+", help="folder containing pictures")
    args = parser.parse_args(argv)
    directory = Path(" ".join(args.directory))

    output_dir = directory / "negative"

    for path in directory.iterdir():
        if path.is_dir():
            continue

        try:
            im = Image.open(path)
        except (UnidentifiedImageError, OSError):
            print(f"Skipping {path.name}: not an image file")
            continue

        # ImageOps.invert only supports "L" (greyscale) and "RGB" - RGBA and
        # palette ("P") images need converting first, which drops any alpha.
        if im.mode not in ("L", "RGB"):
            im = im.convert("RGB")

        im_invert = ImageOps.invert(im)
        output_dir.mkdir(exist_ok=True)
        im_invert.save(output_dir / path.name)
        print(f"Picture {path.name} was changed to negative")


if __name__ == "__main__":
    main()
