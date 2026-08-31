#! python3
# outlook-action - process .msg email files dropped (via drag-and-drop from
# Outlook into a real Explorer folder window - Outlook has no supported way
# to add a right-click item, and a taskbar/.lnk drop target refuses the
# drag) into a configured folder:
#   - a PDF attachment is saved into the output folder
#   - image attachments are saved into the output folder, and also combined
#     into one PDF
#   - a link to a .pdf in the email body is downloaded into the output folder
# Every output file is named "<yyyy-mm-dd> <sender name>[.ext]". Processed
# .msg files are moved into a "processed" subfolder, not deleted.
#
# Run command:
#   outlook-action
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - prompted for and
# saved automatically on first run if missing:
#   outlook:
#     dropFolderName: emails-to-process

import re
import shutil
import sys
from pathlib import Path

import extract_msg
import requests
from PIL import Image

from core.configuration.user_conf import MissingConfigError, load_config_value

DEFAULT_DROP_FOLDER_NAME = "emails-to-process"
OUTPUT_FOLDER_NAME = "output"
PROCESSED_SUBFOLDER_NAME = "processed"

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
PDF_LINK_PATTERN = re.compile(r'https?://\S+?\.pdf(?=[\s"\'<>)]|$)', re.IGNORECASE)


def validate_drop_folder_name(value):
    """Raise ValueError if `value` isn't a plain folder name - this config
    value is a name relative to ~/.boring-stuff, not an arbitrary path."""
    if not value or "/" in value or "\\" in value:
        raise ValueError(f"'{value}' must be a plain folder name, not a path.")


def sanitize_filename_part(text):
    cleaned = INVALID_FILENAME_CHARS.sub("", text).strip()
    return cleaned or "unnamed"


def extract_sender_name(sender):
    """Pull the display name out of a "Name <email>" sender string,
    falling back to the raw value (e.g. a bare email address) if there's no
    "<...>" part."""
    if not sender:
        return "unknown-sender"
    name = sender.split("<")[0].strip().strip('"')
    return name or sender


def unique_path(path):
    """Same collision-avoidance scheme as clipsave.py's unique_path."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def classify_attachment(attachment):
    suffix = Path(attachment.getFilename() or "").suffix.lower()
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return None


def find_message_files(folder):
    return sorted(folder.glob("*.msg"))


def find_pdf_links(text):
    if not text:
        return []
    return PDF_LINK_PATTERN.findall(text)


def gather_searchable_text(msg):
    """Combine the plain-text and HTML bodies into one string to scan for
    PDF links - some emails only carry an HTML body."""
    parts = []
    if msg.body:
        parts.append(msg.body)
    if msg.htmlBody:
        html = msg.htmlBody
        if isinstance(html, bytes):
            html = html.decode("utf-8", errors="ignore")
        parts.append(html)
    return "\n".join(parts)


def save_pdf_attachment(attachment, output_dir, base_name):
    target = unique_path(output_dir / f"{base_name}.pdf")
    target.write_bytes(attachment.data)
    return target


def save_images_and_build_pdf(image_attachments, output_dir, base_name):
    """Save each image attachment as its own file, and also combine all of
    them into a single PDF (via Pillow - already a dependency). Returns the
    list of saved image paths plus the combined PDF path."""
    saved_images = []
    for attachment in image_attachments:
        suffix = Path(attachment.getFilename() or "").suffix.lower() or ".jpg"
        target = unique_path(output_dir / f"{base_name}{suffix}")
        target.write_bytes(attachment.data)
        saved_images.append(target)

    pdf_target = unique_path(output_dir / f"{base_name}.pdf")
    opened = [Image.open(path).convert("RGB") for path in saved_images]
    try:
        opened[0].save(pdf_target, save_all=True, append_images=opened[1:])
    finally:
        for image in opened:
            image.close()

    return saved_images, pdf_target


def download_pdf_link(url, output_dir, base_name):
    target = unique_path(output_dir / f"{base_name}.pdf")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    target.write_bytes(response.content)
    return target


def process_message_file(msg_path, output_dir):
    """Extract PDFs/images/linked PDFs from one .msg file into output_dir.
    Returns the list of saved paths (empty if there was nothing to do)."""
    msg = extract_msg.Message(str(msg_path))
    try:
        sender_name = sanitize_filename_part(extract_sender_name(msg.sender))
        date_str = msg.date.strftime("%Y-%m-%d") if msg.date else "unknown-date"
        base_name = f"{date_str} {sender_name}"

        saved = []

        pdf_attachments = [a for a in msg.attachments if classify_attachment(a) == "pdf"]
        for attachment in pdf_attachments:
            saved.append(save_pdf_attachment(attachment, output_dir, base_name))

        image_attachments = [a for a in msg.attachments if classify_attachment(a) == "image"]
        if image_attachments:
            images, combined_pdf = save_images_and_build_pdf(image_attachments, output_dir, base_name)
            saved.extend(images)
            saved.append(combined_pdf)

        for url in find_pdf_links(gather_searchable_text(msg)):
            try:
                saved.append(download_pdf_link(url, output_dir, base_name))
            except requests.exceptions.RequestException as e:
                print(f"  Could not download {url}: {e}")

        return saved
    finally:
        msg.close()


def main():
    try:
        folder_name = load_config_value(
            None,
            "Emails-to-process folder name (inside ~/.boring-stuff)",
            DEFAULT_DROP_FOLDER_NAME,
            "outlook",
            "dropFolderName",
            validate=validate_drop_folder_name,
        )
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    boring_stuff_dir = Path.home() / ".boring-stuff"
    drop_dir = boring_stuff_dir / folder_name
    output_dir = boring_stuff_dir / OUTPUT_FOLDER_NAME
    processed_dir = drop_dir / PROCESSED_SUBFOLDER_NAME

    drop_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    message_files = find_message_files(drop_dir)
    if not message_files:
        print(f"No .msg files found in {drop_dir}")
        return

    for msg_path in message_files:
        print(f"Processing: {msg_path.name}")
        try:
            saved = process_message_file(msg_path, output_dir)
        except Exception as e:  # noqa: BLE001 - one bad .msg shouldn't stop the rest of the batch
            print(f"  Failed to process {msg_path.name}: {e}")
            continue

        if saved:
            for path in saved:
                print(f"  Saved: {path.name}")
        else:
            print("  Nothing to extract.")

        target = unique_path(processed_dir / msg_path.name)
        shutil.move(str(msg_path), str(target))


if __name__ == "__main__":
    main()
