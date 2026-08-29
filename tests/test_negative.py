from PIL import Image

from cases.pictures import negative


def test_creates_negative_for_each_image(tmp_path, monkeypatch):
    img = Image.new("RGB", (4, 4), color=(10, 20, 30))
    img.save(tmp_path / "pic.png")

    monkeypatch.setattr(negative.sys, "argv", ["negative", str(tmp_path)])
    negative.main()

    out_path = tmp_path / "negativepic.png"
    assert out_path.exists()
    inverted = Image.open(out_path)
    assert inverted.getpixel((0, 0)) == (245, 235, 225)


def test_prints_message_when_no_args(monkeypatch, capsys):
    monkeypatch.setattr(negative.sys, "argv", ["negative"])
    negative.main()

    out = capsys.readouterr().out
    assert "No parameter was inserted." in out
