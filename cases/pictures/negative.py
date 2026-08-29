#! python3


from PIL import Image, ImageOps, UnidentifiedImageError

import sys
import os


def main():
    if len(sys.argv) > 1:
        # Get directory from command line.
        directory = ' '.join(sys.argv[1:])

        for x in os.listdir(directory):
            try:
                im = Image.open(directory + '/' + x)
            except (UnidentifiedImageError, OSError):
                print("Skipping " + x + ": not an image file")
                continue

            im_invert = ImageOps.invert(im)
            im_invert.save(directory + '/negative' + x )
            print("Picture " + x + " was changed to negative")

    else:
        print("No parameter was inserted.")


if __name__ == "__main__":
    main()

