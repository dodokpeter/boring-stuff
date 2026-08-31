from PIL import Image

from core import icon


def test_generate_icon_creates_multi_size_ico(tmp_path):
    icon_path = tmp_path / "sub" / "boring.ico"

    icon.generate_icon(icon_path)

    assert icon_path.exists()
    with Image.open(icon_path) as img:
        assert set(img.info.get("sizes", [])) >= {(16, 16), (32, 32), (48, 48), (256, 256)}


def test_generate_icon_creates_parent_directory(tmp_path):
    icon_path = tmp_path / "does" / "not" / "exist" / "boring.ico"

    icon.generate_icon(icon_path)

    assert icon_path.exists()


def test_generate_icon_overwrites_existing_file(tmp_path):
    icon_path = tmp_path / "boring.ico"
    icon_path.write_bytes(b"not a real icon")

    icon.generate_icon(icon_path)

    with Image.open(icon_path) as img:
        assert {(16, 16), (32, 32)} <= set(img.info.get("sizes", []))
