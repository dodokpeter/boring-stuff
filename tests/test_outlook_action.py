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
    def __init__(self, sender=None, date=None, subject=None, body=None, html_body=None, attachments=None):
        self.sender = sender
        self.date = date
        self.subject = subject
        self.body = body
        self.htmlBody = html_body
        self.attachments = attachments or []
        self.closed = False

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 8, 31, 12, 0, 0)

    monkeypatch.setattr(outlook_action, "datetime", FixedDateTime)


def make_image_bytes(color=(255, 0, 0)):
    from io import BytesIO

    buffer = BytesIO()
    Image.new("RGB", (4, 4), color).save(buffer, "PNG")
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


def test_extract_email_identity():
    msg = FakeMessage(sender="Peter Dodok <peter@example.com>", date=datetime(2026, 8, 25), subject="Hello: World")

    assert outlook_action.extract_email_identity(msg) == ("Peter Dodok", "2026-08-25", "Hello World")


def test_extract_email_identity_falls_back_for_missing_date_and_subject():
    msg = FakeMessage(sender="Peter Dodok <peter@example.com>", date=None, subject=None)

    assert outlook_action.extract_email_identity(msg) == ("Peter Dodok", "unknown-date", "no-subject")


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


def test_find_pdf_links_deduplicates_repeated_urls():
    text = "https://example.com/a.pdf and again https://example.com/a.pdf and https://example.com/b.pdf"
    assert outlook_action.find_pdf_links(text) == [
        "https://example.com/a.pdf",
        "https://example.com/b.pdf",
    ]


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


# --- save_bytes_if_new (the duplicate-content check) ---


def test_save_bytes_if_new_writes_when_nothing_matches(tmp_path):
    target, is_new = outlook_action.save_bytes_if_new(b"content", tmp_path, "2026-08-31 Sender", ".pdf")

    assert is_new is True
    assert target == tmp_path / "2026-08-31 Sender.pdf"
    assert target.read_bytes() == b"content"


def test_save_bytes_if_new_reuses_existing_identical_content(tmp_path):
    existing = tmp_path / "2026-08-31 Sender.pdf"
    existing.write_bytes(b"same content")

    target, is_new = outlook_action.save_bytes_if_new(b"same content", tmp_path, "2026-08-31 Sender", ".pdf")

    assert is_new is False
    assert target == existing
    assert len(list(tmp_path.iterdir())) == 1  # nothing new was written


def test_save_bytes_if_new_writes_a_new_file_when_content_differs(tmp_path):
    (tmp_path / "2026-08-31 Sender.pdf").write_bytes(b"old content")

    target, is_new = outlook_action.save_bytes_if_new(b"new content", tmp_path, "2026-08-31 Sender", ".pdf")

    assert is_new is True
    assert target == tmp_path / "2026-08-31 Sender (1).pdf"


def test_save_bytes_if_new_ignores_files_with_different_suffix(tmp_path):
    (tmp_path / "2026-08-31 Sender.jpg").write_bytes(b"same content")

    target, is_new = outlook_action.save_bytes_if_new(b"same content", tmp_path, "2026-08-31 Sender", ".pdf")

    assert is_new is True
    assert target == tmp_path / "2026-08-31 Sender.pdf"


# --- attachment/link saving ---


def test_save_pdf_attachment_writes_file(tmp_path):
    attachment = FakeAttachment("invoice.pdf", b"%PDF-1.4 fake content")

    target, is_new = outlook_action.save_pdf_attachment(attachment, tmp_path, "2026-08-31 Sender")

    assert is_new is True
    assert target == tmp_path / "2026-08-31 Sender.pdf"
    assert target.read_bytes() == b"%PDF-1.4 fake content"


def test_save_pdf_attachment_deduped_on_repeat_call(tmp_path):
    attachment = FakeAttachment("invoice.pdf", b"%PDF-1.4 fake content")

    first, first_is_new = outlook_action.save_pdf_attachment(attachment, tmp_path, "2026-08-31 Sender")
    second, second_is_new = outlook_action.save_pdf_attachment(attachment, tmp_path, "2026-08-31 Sender")

    assert first_is_new is True
    assert second_is_new is False
    assert first == second
    assert len(list(tmp_path.glob("*.pdf"))) == 1


def test_save_images_and_build_pdf(tmp_path):
    attachments = [
        FakeAttachment("one.png", make_image_bytes((255, 0, 0))),
        FakeAttachment("two.png", make_image_bytes((0, 255, 0))),
    ]

    image_results, pdf_result = outlook_action.save_images_and_build_pdf(attachments, tmp_path, "2026-08-31 Sender")

    assert [path for path, _is_new in image_results] == [
        tmp_path / "2026-08-31 Sender.png",
        tmp_path / "2026-08-31 Sender (1).png",
    ]
    assert all(is_new for _path, is_new in image_results)
    for path, _is_new in image_results:
        assert path.exists()

    pdf_path, pdf_is_new = pdf_result
    assert pdf_path == tmp_path / "2026-08-31 Sender.pdf"
    assert pdf_is_new is True
    assert pdf_path.exists()


def test_save_images_and_build_pdf_dedupes_identical_images(tmp_path):
    same_image = make_image_bytes()
    attachments = [FakeAttachment("one.png", same_image), FakeAttachment("two.png", same_image)]

    image_results, _pdf_result = outlook_action.save_images_and_build_pdf(attachments, tmp_path, "2026-08-31 Sender")

    assert [path for path, _is_new in image_results] == [
        tmp_path / "2026-08-31 Sender.png",
        tmp_path / "2026-08-31 Sender.png",
    ]
    assert [is_new for _path, is_new in image_results] == [True, False]
    assert len(list(tmp_path.glob("*.png"))) == 1


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

    target, is_new = outlook_action.download_pdf_link("https://example.com/f.pdf", tmp_path, "2026-08-31 Sender")

    assert is_new is True
    assert target == tmp_path / "2026-08-31 Sender.pdf"
    assert target.read_bytes() == b"%PDF-1.4 downloaded"
    assert calls == [("https://example.com/f.pdf", 30)]


# --- process_message_file ---


def test_process_message_file_saves_pdf_attachment(tmp_path, monkeypatch):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        subject="Invoice",
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved, sender_name, sent_date_str, subject = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == [tmp_path / "2026-08-31 Peter Dodok.pdf"]
    assert (sender_name, sent_date_str, subject) == ("Peter Dodok", "2026-08-31", "Invoice")
    assert msg.closed is True


def test_process_message_file_saves_images_and_combined_pdf(tmp_path, monkeypatch):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        attachments=[FakeAttachment("photo.jpg", make_image_bytes())],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved, *_ = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

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

    saved, *_ = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

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

    saved, *_ = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == []
    assert "Could not download" in capsys.readouterr().out


def test_process_message_file_returns_empty_when_nothing_to_extract(tmp_path, monkeypatch):
    msg = FakeMessage(sender="Peter Dodok <peter@example.com>", date=datetime(2026, 8, 31))
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved, *_ = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)
    assert saved == []


def test_process_message_file_uses_unknown_date_when_missing(tmp_path, monkeypatch):
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=None,
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    saved, *_ = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert saved == [tmp_path / "unknown-date Peter Dodok.pdf"]


def test_process_message_file_only_downloads_a_repeated_link_once(tmp_path, monkeypatch):
    """Regression test: a real email had one PDF attachment and a link to
    that same PDF repeated 3 times across the plain-text and HTML bodies -
    it must not trigger 3 separate downloads (or 3 duplicate output files),
    just the one for the de-duplicated link (whose content then matches the
    attachment already saved, so it doesn't add a second output file)."""
    link = "https://example.com/report.pdf"
    same_content = b"%PDF-1.4 same content"
    msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 31),
        attachments=[FakeAttachment("report.pdf", same_content)],
        body=f"See {link}",
        html_body=f"<a href='{link}'>See {link}</a>".encode(),
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: msg)

    class FakeResponse:
        content = same_content

        def raise_for_status(self):
            pass

    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return FakeResponse()

    monkeypatch.setattr(outlook_action.requests, "get", fake_get)

    saved, *_ = outlook_action.process_message_file(tmp_path / "email.msg", tmp_path)

    assert calls == [link]  # de-duplicated to a single download, not 3
    assert saved == [tmp_path / "2026-08-31 Peter Dodok.pdf"]  # download matched the attachment - no 2nd file
    assert len(list(tmp_path.glob("*.pdf"))) == 1


def test_process_message_file_does_not_duplicate_already_saved_attachment(tmp_path, monkeypatch, capsys):
    def make_msg():
        return FakeMessage(
            sender="Peter Dodok <peter@example.com>",
            date=datetime(2026, 8, 31),
            subject="Invoice",
            attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4 same content")],
        )

    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: make_msg())

    first_saved, *_ = outlook_action.process_message_file(tmp_path / "email1.msg", tmp_path)
    second_saved, *_ = outlook_action.process_message_file(tmp_path / "email2.msg", tmp_path)

    assert first_saved == [tmp_path / "2026-08-31 Peter Dodok.pdf"]
    assert second_saved == []  # already there - nothing new
    assert len(list(tmp_path.glob("*.pdf"))) == 1
    assert "Duplicate, already saved as" in capsys.readouterr().out


# --- main ---


def test_main_processes_and_renames_processed_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(outlook_action.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(outlook_action, "load_config_value", lambda *args, **kwargs: "emails-to-process")

    drop_dir = tmp_path / ".boring-stuff" / "emails-to-process"
    drop_dir.mkdir(parents=True)
    msg_path = drop_dir / "email.msg"
    msg_path.write_bytes(b"fake msg bytes")

    fake_msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 25),
        subject="Hello: World",
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: fake_msg)

    outlook_action.main()

    output_dir = tmp_path / ".boring-stuff" / "output"
    assert (output_dir / "2026-08-25 Peter Dodok.pdf").exists()

    processed_path = drop_dir / "processed" / "2026-08-31 Peter Dodok 2026-08-25 Hello World.msg"
    assert processed_path.exists()
    assert not msg_path.exists()

    out = capsys.readouterr().out
    assert "Processing: email.msg" in out
    assert "Saved: 2026-08-25 Peter Dodok.pdf" in out


def test_main_reports_when_no_messages_found(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(outlook_action.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(outlook_action, "load_config_value", lambda *args, **kwargs: "emails-to-process")

    outlook_action.main()

    assert "No .msg files found" in capsys.readouterr().out


def test_main_reports_and_still_moves_file_when_duplicate(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(outlook_action.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(outlook_action, "load_config_value", lambda *args, **kwargs: "emails-to-process")

    drop_dir = tmp_path / ".boring-stuff" / "emails-to-process"
    drop_dir.mkdir(parents=True)
    output_dir = tmp_path / ".boring-stuff" / "output"
    output_dir.mkdir(parents=True)
    (output_dir / "2026-08-25 Peter Dodok.pdf").write_bytes(b"%PDF-1.4")

    msg_path = drop_dir / "email.msg"
    msg_path.write_bytes(b"fake msg bytes")
    fake_msg = FakeMessage(
        sender="Peter Dodok <peter@example.com>",
        date=datetime(2026, 8, 25),
        subject="Hello",
        attachments=[FakeAttachment("invoice.pdf", b"%PDF-1.4")],
    )
    monkeypatch.setattr(outlook_action.extract_msg, "Message", lambda path: fake_msg)

    outlook_action.main()

    assert len(list(output_dir.glob("*.pdf"))) == 1  # still just the one
    assert not msg_path.exists()  # moved anyway, so it's not reprocessed next run

    out = capsys.readouterr().out
    assert "Duplicate, already saved as" in out
    assert "Nothing new to extract." in out


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
