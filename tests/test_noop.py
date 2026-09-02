import pytest

from cases.devs import noop


def test_main_exits_cleanly_with_no_args():
    noop.main([])  # must not raise, must not sys.exit


def test_main_ignores_unrelated_arguments():
    noop.main(["--whatever", "some", "arg"])  # must not raise


def test_main_fail_flag_writes_to_stderr_and_exits_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        noop.main(["--fail"])

    assert exc_info.value.code == 1
    assert "failing as requested" in capsys.readouterr().err
