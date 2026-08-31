import pytest

from core import stats


@pytest.fixture(autouse=True)
def isolated_usage_stats(tmp_path, monkeypatch):
    """Every test gets its own throwaway ~/.boring-stuff/usage.jsonl -
    running the test suite must never write into the real one, since
    (almost) every command's main() now calls record_usage()."""
    monkeypatch.setattr(stats.Path, "home", lambda: tmp_path)
    return tmp_path
