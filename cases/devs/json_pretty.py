#! python3
# json-pretty - pretty-print (or minify) the clipboard's JSON text, in
# place - result goes straight back onto the clipboard.
#
# json-pretty            pretty-print (2-space indent)
# json-pretty --minify   minify (no whitespace)

import argparse
import json
import sys

import pyperclip


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pretty-print or minify the clipboard's JSON text")
    parser.add_argument("-m", "--minify", action="store_true", help="minify instead of pretty-printing")
    args = parser.parse_args(argv)

    text = pyperclip.paste()
    if not text:
        print("Clipboard is empty or contains no text.")
        sys.exit(1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Clipboard content is not valid JSON: {e}")
        sys.exit(1)

    if args.minify:
        formatted = json.dumps(data, separators=(",", ":"))
    else:
        formatted = json.dumps(data, indent=2)

    pyperclip.copy(formatted)
    action = "Minified" if args.minify else "Pretty-printed"
    print(f"{action} and copied to clipboard:")
    print(formatted)


if __name__ == "__main__":
    main()
