import subprocess

import pytest

from cases.devs import prune_branches


def git(*args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def branch_names(repo):
    return git("branch", "--format=%(refname:short)", cwd=repo).split()


@pytest.fixture
def repo(tmp_path):
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"
    git("init", "--bare", "-b", "master", str(remote), cwd=tmp_path)
    git("clone", str(remote), str(local), cwd=tmp_path)
    git("config", "user.email", "test@example.com", cwd=local)
    git("config", "user.name", "Test", cwd=local)
    (local / "README.md").write_text("init", encoding="utf-8")
    git("add", "README.md", cwd=local)
    git("commit", "-m", "init", cwd=local)
    git("push", "-u", "origin", "master", cwd=local)
    return local


def make_merged_branch(repo, name):
    git("checkout", "-b", name, cwd=repo)
    (repo / f"{name}.txt").write_text(name, encoding="utf-8")
    git("add", f"{name}.txt", cwd=repo)
    git("commit", "-m", name, cwd=repo)
    git("checkout", "master", cwd=repo)
    git("merge", "--no-ff", "-m", f"merge {name}", name, cwd=repo)
    git("push", "origin", "master", cwd=repo)


def test_dry_run_lists_but_does_not_delete(repo, monkeypatch, capsys):
    make_merged_branch(repo, "feature-a")

    monkeypatch.chdir(repo)
    prune_branches.main([])

    assert "feature-a" in branch_names(repo)
    out = capsys.readouterr().out
    assert "feature-a" in out
    assert "Dry run" in out


def test_yes_deletes_merged_branch(repo, monkeypatch):
    make_merged_branch(repo, "feature-b")

    monkeypatch.chdir(repo)
    prune_branches.main(["--yes"])

    assert "feature-b" not in branch_names(repo)


def test_does_not_delete_unmerged_branch(repo, monkeypatch):
    git("checkout", "-b", "feature-c", cwd=repo)
    (repo / "feature-c.txt").write_text("c", encoding="utf-8")
    git("add", "feature-c.txt", cwd=repo)
    git("commit", "-m", "feature-c", cwd=repo)
    git("checkout", "master", cwd=repo)

    monkeypatch.chdir(repo)
    prune_branches.main(["--yes"])

    assert "feature-c" in branch_names(repo)


def test_reports_when_nothing_to_prune(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    prune_branches.main([])

    out = capsys.readouterr().out
    assert "No local branches to prune" in out
