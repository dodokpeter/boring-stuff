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
