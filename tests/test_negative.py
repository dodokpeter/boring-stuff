import pytest
from PIL import Image

from cases.pictures import negative


def test_creates_negative_for_each_image_in_a_subfolder(tmp_path):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    img.save(tmp_path / "pic.png")

    negative.main([str(tmp_path)])

    out_path = tmp_path / "negative" / "pic.png"
    assert out_path.exists()
    inverted = Image.open(out_path)
    assert inverted.getpixel((0, 0)) == (245, 235, 225)


def test_second_run_does_not_reinvert_its_own_output(tmp_path):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    img.save(tmp_path / "pic.png")

    negative.main([str(tmp_path)])
    negative.main([str(tmp_path)])

    out_path = tmp_path / "negative" / "pic.png"
    inverted = Image.open(out_path)
    assert inverted.getpixel((0, 0)) == (245, 235, 225)


def test_converts_rgba_images_before_inverting(tmp_path):
    img = Image.new("RGBA", (4, 4), color=(10, 20, 30, 255))
    img.save(tmp_path / "pic.png")

    negative.main([str(tmp_path)])

    out_path = tmp_path / "negative" / "pic.png"
    inverted = Image.open(out_path)
    assert inverted.convert("RGB").getpixel((0, 0)) == (245, 235, 225)


def test_skips_non_image_files_instead_of_crashing(tmp_path, capsys):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    img.save(tmp_path / "pic.png")
    (tmp_path / "notes.txt").write_text("not an image")

    negative.main([str(tmp_path)])

    out_path = tmp_path / "negative" / "pic.png"
    assert out_path.exists()

    out = capsys.readouterr().out
    assert "Skipping notes.txt" in out
    assert "pic.png was changed to negative" in out


def test_no_folder_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        negative.main([])
    assert exc_info.value.code == 2


def test_prints_message_and_returns_when_path_does_not_exist(tmp_path, capsys):
    negative.main([str(tmp_path / "nope")])  # must not raise

    assert "does not exist" in capsys.readouterr().out


def test_single_file_creates_negative_in_parent_folder(tmp_path):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    pic_path = tmp_path / "pic.png"
    img.save(pic_path)

    negative.main([str(pic_path)])

    out_path = tmp_path / "negative" / "pic.png"
    assert out_path.exists()
    inverted = Image.open(out_path)
    assert inverted.getpixel((0, 0)) == (245, 235, 225)


def test_single_file_does_not_touch_sibling_files(tmp_path):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    target_path = tmp_path / "pic.png"
    img.save(target_path)
    sibling = Image.new("RGB", (4, 4), color=(1, 2, 3))
    sibling.save(tmp_path / "sibling.png")

    negative.main([str(target_path)])

    assert (tmp_path / "negative" / "pic.png").exists()
    assert not (tmp_path / "negative" / "sibling.png").exists()


def test_single_non_image_file_prints_message_without_creating_folder(tmp_path, capsys):
    text_path = tmp_path / "notes.txt"
    text_path.write_text("not an image")

    negative.main([str(text_path)])

    assert "Skipping notes.txt" in capsys.readouterr().out
    assert not (tmp_path / "negative").exists()
