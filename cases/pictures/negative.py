#! python3
# negative - invert a picture (or every picture in a folder) to its
# negative, saved into a "negative" subfolder alongside the original(s) (so
# a second run doesn't invert its own output).
#
# negative <picture>   invert just that one picture
# negative <folder>    invert every picture in the folder

import argparse
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from core.stats import record_usage


def invert_one(path, output_dir):
    """Invert the image at `path` and save it into output_dir (creating it
    if needed). Returns True if it was a valid image, False (with a
    message printed) otherwise."""
    try:
        im = Image.open(path)
    except (UnidentifiedImageError, OSError):
        print(f"Skipping {path.name}: not an image file")
        return False

    # ImageOps.invert only supports "L" (greyscale) and "RGB" - RGBA and
    # palette ("P") images need converting first, which drops any alpha.
    if im.mode not in ("L", "RGB"):
        im = im.convert("RGB")

    im_invert = ImageOps.invert(im)
    output_dir.mkdir(exist_ok=True)
    im_invert.save(output_dir / path.name)
    print(f"Picture {path.name} was changed to negative")
    return True


def main(argv=None):
    record_usage("negative")
    parser = argparse.ArgumentParser(description="Invert a picture (or every picture in a folder) to its negative")
    parser.add_argument("path", nargs="+", help="a picture file, or a folder containing pictures")
    args = parser.parse_args(argv)
    path = Path(" ".join(args.path))

    if not path.exists():
        print(f"'{path}' does not exist.")
        return

    if path.is_file():
        invert_one(path, path.parent / "negative")
        return

    output_dir = path / "negative"
    for entry in path.iterdir():
        if entry.is_dir():
            continue
        invert_one(entry, output_dir)


if __name__ == "__main__":
    main()
