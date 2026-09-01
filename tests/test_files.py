from core import files


def test_unique_path_returns_original_when_free(tmp_path):
    target = tmp_path / "file.pdf"
    assert files.unique_path(target) == target


def test_unique_path_appends_counter_on_collision(tmp_path):
    (tmp_path / "file.pdf").write_bytes(b"")
    (tmp_path / "file (1).pdf").write_bytes(b"")

    assert files.unique_path(tmp_path / "file.pdf") == tmp_path / "file (2).pdf"
