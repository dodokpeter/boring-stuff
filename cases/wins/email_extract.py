#! python3
# email-extract - process .msg email files dropped (via drag-and-drop from
# Outlook into a real Explorer folder window - Outlook has no supported way
# to add a right-click item, and a taskbar/.lnk drop target refuses the
# drag) into a configured folder:
#   - a PDF attachment is saved into the output folder
#   - image attachments are saved into the output folder, and also combined
#     into one PDF
#   - a link to a .pdf in the email body is downloaded into the output folder
# Every output file is named "<yyyy-mm-dd> <sender name>[.ext]". Before
# writing, each piece of content is hash-checked against what's already in
# the output folder (same sender/date) so dropping the same email more than
# once doesn't produce repeat copies. Processed .msg files are moved into a
# "processed" subfolder (not deleted), renamed to
# "<yyyy-mm-dd processed> <sender name> <yyyy-mm-dd sent> <subject>.msg".
#
# Run command:
#   email-extract
#
# Configuration (in ~/.boring-stuff/BoringStuff.yml) - prompted for and
# saved automatically on first run if missing:
#   outlook:
#     dropFolderName: emails-to-process

import hashlib
import re
import shutil
import sys
from datetime import datetime
from io import BytesIO
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


def extract_email_identity(msg):
    """Return (sender_name, sent_date_str, subject), each already
    filesystem-sanitized - used both for output filenames and the
    processed-folder rename."""
    sender_name = sanitize_filename_part(extract_sender_name(msg.sender))
    sent_date_str = msg.date.strftime("%Y-%m-%d") if msg.date else "unknown-date"
    subject = sanitize_filename_part(msg.subject or "no-subject")
    return sender_name, sent_date_str, subject


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


def save_bytes_if_new(data, output_dir, base_name, suffix):
    """Write `data` to output_dir as "<base_name><suffix>" (or a
    collision-numbered variant), unless a file already there whose name
    starts with `base_name` and ends with `suffix` has the exact same
    content - in which case that existing file is reused and nothing new
    is written. This is what stops the same email (dropped more than once,
    or reprocessed) from producing repeat output files.

    Returns (path, is_new)."""
    digest = hashlib.sha256(data).hexdigest()
    for existing in output_dir.iterdir():
        if not existing.is_file():
            continue
        if not (existing.name.startswith(base_name) and existing.name.endswith(suffix)):
            continue
        if hashlib.sha256(existing.read_bytes()).hexdigest() == digest:
            return existing, False

    target = unique_path(output_dir / f"{base_name}{suffix}")
    target.write_bytes(data)
    return target, True


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
    """Extract .pdf links, de-duplicated (preserving order) - the same
    link commonly appears more than once (e.g. in both the plain-text and
    HTML versions of a body), and there's no point downloading it twice."""
    if not text:
        return []
    return list(dict.fromkeys(PDF_LINK_PATTERN.findall(text)))


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
    return save_bytes_if_new(attachment.data, output_dir, base_name, ".pdf")


def save_images_and_build_pdf(image_attachments, output_dir, base_name):
    """Save each image attachment (deduped against existing output
    content), and also combine all of them into a single PDF (via Pillow -
    already a dependency; also deduped). Returns (image_results,
    pdf_result), each a (path, is_new) pair or list of pairs."""
    image_results = []
    for attachment in image_attachments:
        suffix = Path(attachment.getFilename() or "").suffix.lower() or ".jpg"
        image_results.append(save_bytes_if_new(attachment.data, output_dir, base_name, suffix))

    opened = [Image.open(path).convert("RGB") for path, _is_new in image_results]
    try:
        buffer = BytesIO()
        opened[0].save(buffer, format="PDF", save_all=True, append_images=opened[1:])
    finally:
        for image in opened:
            image.close()

    pdf_result = save_bytes_if_new(buffer.getvalue(), output_dir, base_name, ".pdf")
    return image_results, pdf_result


def download_pdf_link(url, output_dir, base_name):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return save_bytes_if_new(response.content, output_dir, base_name, ".pdf")


def report_save(path, is_new):
    if is_new:
        print(f"  Saved: {path.name}")
    else:
        print(f"  Duplicate, already saved as: {path.name}")


def process_message_file(msg_path, output_dir):
    """Extract PDFs/images/linked PDFs from one .msg file into output_dir.
    Returns (saved, sender_name, sent_date_str, subject) - `saved` is the
    list of newly-created paths (empty if there was nothing new to do;
    duplicates of existing output are reported but not included)."""
    msg = extract_msg.Message(str(msg_path))
    try:
        sender_name, sent_date_str, subject = extract_email_identity(msg)
        base_name = f"{sent_date_str} {sender_name}"

        saved = []

        pdf_attachments = [a for a in msg.attachments if classify_attachment(a) == "pdf"]
        for attachment in pdf_attachments:
            path, is_new = save_pdf_attachment(attachment, output_dir, base_name)
            report_save(path, is_new)
            if is_new:
                saved.append(path)

        image_attachments = [a for a in msg.attachments if classify_attachment(a) == "image"]
        if image_attachments:
            image_results, pdf_result = save_images_and_build_pdf(image_attachments, output_dir, base_name)
            for path, is_new in image_results:
                report_save(path, is_new)
                if is_new:
                    saved.append(path)
            report_save(*pdf_result)
            if pdf_result[1]:
                saved.append(pdf_result[0])

        for url in find_pdf_links(gather_searchable_text(msg)):
            try:
                path, is_new = download_pdf_link(url, output_dir, base_name)
                report_save(path, is_new)
                if is_new:
                    saved.append(path)
            except requests.exceptions.RequestException as e:
                print(f"  Could not download {url}: {e}")

        return saved, sender_name, sent_date_str, subject
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
            saved, sender_name, sent_date_str, subject = process_message_file(msg_path, output_dir)
        except Exception as e:  # noqa: BLE001 - one bad .msg shouldn't stop the rest of the batch
            print(f"  Failed to process {msg_path.name}: {e}")
            continue

        if not saved:
            print("  Nothing new to extract.")

        processed_date_str = datetime.now().strftime("%Y-%m-%d")
        processed_name = f"{processed_date_str} {sender_name} {sent_date_str} {subject}.msg"
        target = unique_path(processed_dir / processed_name)
        shutil.move(str(msg_path), str(target))


if __name__ == "__main__":
    main()
