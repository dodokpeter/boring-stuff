import pytest

from wins import base64_clip


@pytest.fixture
def clipboard(monkeypatch):
    state = {"value": ""}
    monkeypatch.setattr(base64_clip.pyperclip, "paste", lambda: state["value"])
    monkeypatch.setattr(base64_clip.pyperclip, "copy", lambda text: state.__setitem__("value", text))
    return state


def test_decode_valid_base64(clipboard):
    clipboard["value"] = "aGVsbG8gYmFzZTY0IHdvcmxk"

    base64_clip.main_decode()

    assert clipboard["value"] == "hello base64 world"


def test_decode_tolerates_wrapped_lines(clipboard):
    # base64 blobs (e.g. copied from a PEM file) are often wrapped across
    # multiple lines - internal whitespace shouldn't break decoding.
    clipboard["value"] = "aGVsbG8g\nYmFzZTY0\nIHdvcmxk"

    base64_clip.main_decode()

    assert clipboard["value"] == "hello base64 world"


def test_decode_rejects_invalid_base64(clipboard):
    clipboard["value"] = "this is definitely not valid base64!!"

    with pytest.raises(SystemExit):
        base64_clip.main_decode()

    # clipboard is left untouched on failure
    assert clipboard["value"] == "this is definitely not valid base64!!"


def test_decode_rejects_non_utf8_result(clipboard):
    # valid base64, but decodes to bytes that aren't valid UTF-8 text
    clipboard["value"] = "gA=="  # decodes to b'\x80'

    with pytest.raises(SystemExit):
        base64_clip.main_decode()


def test_decode_exits_on_empty_clipboard(clipboard):
    clipboard["value"] = ""

    with pytest.raises(SystemExit):
        base64_clip.main_decode()


def test_encode_round_trips_with_decode(clipboard):
    clipboard["value"] = "hello base64 world"

    base64_clip.main_encode()
    assert clipboard["value"] == "aGVsbG8gYmFzZTY0IHdvcmxk"

    base64_clip.main_decode()
    assert clipboard["value"] == "hello base64 world"


def test_encode_exits_on_empty_clipboard(clipboard):
    clipboard["value"] = ""

    with pytest.raises(SystemExit):
        base64_clip.main_encode()
