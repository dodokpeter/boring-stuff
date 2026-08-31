from datetime import datetime

import pytest
import requests
from PIL import Image

from cases.wins import outlook_action


class FakeAttachment:
    def __init__(self, filename, data):
        self._filename = filename
        self.data = data

    def getFilename(self):
        return self._filename


class FakeMessage:
    def __init__(self, sender=None, date=None, body=None, html_body=None, attachments=None):
        self.sender = sender
        self.date = date
        self.body = body
        self.htmlBody = html_body
        self.attachments = attachments or []
        self.closed = False

    def close(self):
        self.closed = True


def make_image_bytes():
    from io import BytesIO

    buffer = BytesIO()
    Image.new("RGB", (4, 4), (255, 0, 0)).save(buffer, "PNG")
    return buffer.getvalue()


# --- pure helper functions ---


def test_extract_sender_name_from_name_and_email():
    assert outlook_action.extract_sender_name("Peter Dodok <peter@example.com>") == "Peter Dodok"


def test_extract_sender_name_falls_back_to_raw_value_without_angle_brackets():
    assert outlook_action.extract_sender_name("peter@example.com") == "peter@example.com"


def test_extract_sender_name_handles_missing_sender():
    assert outlook_action.extract_sender_name(None) == "unknown-sender"


def test_extract_sender_name_strips_quotes():
    assert outlook_action.extract_sender_name('"Peter Dodok" <peter@example.com>') == "Peter Dodok"


def test_sanitize_filename_part_removes_invalid_characters():
    assert outlook_action.sanitize_filename_part("Some: Name / With * Bad? Chars") == "Some Name  With  Bad Chars"


def test_sanitize_filename_part_falls_back_when_empty():
    assert outlook_action.sanitize_filename_part("///") == "unnamed"


def test_classify_attachment_pdf():
    assert outlook_action.classify_attachment(FakeAttachment("invoice.PDF", b"")) == "pdf"


def test_classify_attachment_image():
    assert outlook_action.classify_attachment(FakeAttachment("photo.jpg", b"")) == "image"


def test_classify_attachment_other():
    assert outlook_action.classify_attachment(FakeAttachment("notes.docx", b"")) is None


def test_find_pdf_links_extracts_urls_from_text():
    text = 'See https://example.com/report.pdf for details, or "https://example.com/other.pdf" here.'
    assert outlook_action.find_pdf_links(text) == [
        "https://example.com/report.pdf",
        "https://example.com/other.pdf",
    ]


def test_find_pdf_links_returns_empty_for_no_links():
    assert outlook_action.find_pdf_links("no links here") == []


def test_find_pdf_links_handles_none():
    assert outlook_action.find_pdf_links(None) == []


def test_unique_path_returns_original_when_free(tmp_path):
    target = tmp_path / "file.pdf"
    assert outlook_action.unique_path(target) == target


def test_unique_path_appends_counter_on_collision(tmp_path):
    (tmp_path / "file.pdf").write_bytes(b"")
    (tmp_path / "file (1).pdf").write_bytes(b"")

    assert outlook_action.unique_path(tmp_path / "file.pdf") == tmp_path / "file (2).pdf"


def test_gather_searchable_text_combines_body_and_html():
    msg = FakeMessage(body="plain text body", html_body=b"<p>html body</p>")
    text = outlook_action.gather_searchable_text(msg)
    assert "plain text body" in text
    assert "html body" in text


def test_validate_drop_folder_name_rejects_path_separators():
    with pytest.raises(ValueError):
        outlook_action.validate_drop_folder_name("some/path")
    with pytest.raises(ValueError):
        outlook_action.validate_drop_folder_name("some\\path")


def test_validate_drop_folder_name_accepts_plain_name():
    outlook_action.validate_drop_folder_name("emails-to-process")  # does not raise


# --- attachment/link saving ---


def test_save_pdf_attachment_writes_file(tmp_path):
    attachment = FakeAttachment("invoice.pdf", b"%PDF-1.4 fake content")

    target = outlook_action.save_pdf_attachment(attachment, tmp_path, "2026-08-31 Sender")

    assert target == tmp_path / "2026-08-31 Sender.pdf"
    assert target.read_bytes() == b"%PDF-1.4 fake content"


def test_save_images_and_build_pdf(tmp_path):
    image_bytes = make_image_bytes()
    attachments = [FakeAttachment("one.png", image_bytes), FakeAttachment("two.png", image_bytes)]

    saved_images, pdf_path = outlook_action.save_images_and_build_pdf(attachments, tmp_path, "2026-08-31 Sender")

    assert saved_images == [
        tmp_path / "2026-08-31 Sender.png",
        tmp_path / "2026-08-31 Sender (1).png",
    ]
    for image_path in saved_images:
        assert image_path.exists()

    assert pdf_path == tmp_path / "2026-08-31 Sender.pdf"
    assert pdf_path.exists()


def test_download_pdf_link_writes_file(tmp_path, monkeypatch):
    class FakeResponse:
        content = b"%PDF-1.4 downloaded"

        def raise_for_status(self):
            pass

    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse()

    monkeypatch.setattr(outlook_action.requests, "get", fake_get)

    target = outlook_action.download_pdf_link("https://example.com/f.pdf", tmp_path, "2026-08-31 Sender")

    assert target == tmp_path / "2026-08-31 Sender.pdf"
    assert target.read_bytes() == b"%PDF-1.4 downloaded"
    assert calls == [("https://example.com/f.pdf", 30)]


# --- process_message_file ---


def test_process_message_file_saves_pdf_attachment(tmp_path, monkeypatch):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == [tmp_path / "2026-08-31 Peter Dodok.pdf"]
    assert msg.closed is True


def test_process_message_file_saves_images_and_combined_pdf(tmp_path, monkeypatch):
    image_bytes = make_image_bytes()
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        attachments=[FakeAttachment("photo.jpg", image_bytes)],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == [
        tmp_path / "2026-08-31 Peter Dodok.jpg",
        tmp_path / "2026-08-31 Peter Dodok.pdf",
    ]


def test_process_message_file_downloads_pdf_link(tmp_path, monkeypatch):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        body="Report here: https://example.com/report.pdf",
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    class FakeResponse:
        content = b"%PDF-1.4 downloaded"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(outlook_action.requests, "get", lambda url, timeout: FakeResponse())

    saved = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == [tmp_path / "2026-08-31 Peter Dodok.pdf"]


def test_process_message_file_continues_when_download_fails(tmp_path, monkeypatch, capsys):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        body="Report here: https://example.com/report.pdf",
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    def raise_connection_error(url, timeout):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(outlook_action.requests, "get", raise_connection_error)

    saved = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == []
    assert "Could not download" in capsys.readouterr().out


def test_process_message_file_returns_empty_when_nothing_to_extract(tmp_path, monkeypatch):
    msg = FakeMessage(sender="Peter Dodok <peter@example.com>", date=datetime(2026, 8, 31))
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    assert outlook_action.process_message_file(tmp_path / "email.msg", tmp_path) == []


def test_process_message_file_uses_unknown_date_when_missing(tmp_path, monkeypatch):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=None,
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == [tmp_path / "unknown-date Peter Dodok.pdf"]


# --- main ---


def test_main_processes_and_moves_message_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(outlook_action.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(outlook_action, "load_config_value", lambda *args, **kwargs: "emails-to-process")

    drop_dir = tmp_path / ".boring-stuff" / "emails-to-process"
    drop_dir.mkdir(parents=True)
    msg_path = drop_dir / "email.msg"
    msg_path.write_bytes(b"fake msg bytes")

    fake_msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: fake_msg)

    outlook_action.main()

    output_dir = tmp_path / ".boring-stuff" / "output"
    assert (output_dir / "2026-08-31 Peter Dodok.pdf").exists()

    processed_path = drop_dir / "processed" / "email.msg"
    assert processed_path.exists()
    assert not msg_path.exists()

    out = capsys.readouterr().out
    assert "Processing: email.msg" in out
    assert "Saved: 2026-08-31 Peter Dodok.pdf" in out


def test_main_reports_when_no_messages_found(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(outlook_action.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(outlook_action, "load_config_value", lambda *args, **kwargs: "emails-to-process")

    outlook_action.main()

    assert "No .msg files found" in capsys.readouterr().out


def test_main_continues_after_a_processing_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(outlook_action.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(outlook_action, "load_config_value", lambda *args, **kwargs: "emails-to-process")

    drop_dir = tmp_path / ".boring-stuff" / "emails-to-process"
    drop_dir.mkdir(parents=True)
    (drop_dir / "broken.msg").write_bytes(b"")

    def raise_error(path):
        raise ValueError("corrupt file")

    monkeypatch.setattr(outlook_action.extract_msg, "Message", raise_error)

    outlook_action.main()

    assert "Failed to process broken.msg" in capsys.readouterr().out
    assert (drop_dir / "broken.msg").exists()  # left in place, not moved


def test_main_exits_cleanly_when_config_cannot_be_obtained(monkeypatch, capsys):
    def raise_missing(*args, **kwargs):
        raise outlook_action.MissingConfigError("dropFolderName is not configured, and no terminal is attached.")

    monkeypatch.setattr(outlook_action, "load_config_value", raise_missing)

    with pytest.raises(SystemExit):
        outlook_action.main()

    assert "not configured" in capsys.readouterr().out
