#! python3
# b64d / b64e - base64 decode/encode the clipboard's text and write the
# result straight back to the clipboard. No files, no arguments.
#
# b64d   decode clipboard text from base64
# b64e   encode clipboard text into base64

import base64
import binascii
import sys

import pyperclip

from core.stats import record_usage


def main_decode():
    record_usage("b64d")
    text = pyperclip.paste()
    if not text:
        print("Clipboard is empty or contains no text.")
        sys.exit(1)

    condensed = "".join(text.split())
    try:
        decoded_bytes = base64.b64decode(condensed, validate=True)
    except binascii.Error as e:
        print(f"Clipboard content is not valid base64: {e}")
        sys.exit(1)

    try:
        decoded_text = decoded_bytes.decode("utf-8")
    except UnicodeDecodeError:
        print("Decoded successfully, but the result isn't valid UTF-8 text - can't place it on the clipboard.")
        sys.exit(1)

    pyperclip.copy(decoded_text)
    print("Decoded and copied to clipboard:")
    print(decoded_text)


def main_encode():
    record_usage("b64e")
    text = pyperclip.paste()
    if not text:
        print("Clipboard is empty or contains no text.")
        sys.exit(1)

    encoded_text = base64.b64encode(text.encode("utf-8")).decode("ascii")

    pyperclip.copy(encoded_text)
    print("Encoded and copied to clipboard:")
    print(encoded_text)
