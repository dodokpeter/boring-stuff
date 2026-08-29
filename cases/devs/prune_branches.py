#! python3
# prune-branches - delete local git branches already merged into
# origin's default branch (master/main). Dry-run by default.
#
# prune-branches          list branches that would be deleted
# prune-branches --yes    actually delete them

import argparse
import subprocess
import sys


def run(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def get_default_branch():
    result = run("symbolic-ref", "refs/remotes/origin/HEAD")
    if result.returncode == 0:
        return result.stdout.strip().rsplit("/", 1)[-1]
    for candidate in ("main", "master"):
        check = run("show-ref", "--verify", "--quiet", f"refs/remotes/origin/{candidate}")
        if check.returncode == 0:
            return candidate
    return None


def get_current_branch():
    return run("branch", "--show-current").stdout.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Delete local branches already merged into origin's default branch")
    parser.add_argument("--yes", "-y", action="store_true", help="actually delete (default is a dry run)")
    args = parser.parse_args(argv)

    if run("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("Not inside a git repository.")
        sys.exit(1)

    print("Fetching from origin...")
    fetch = run("fetch", "origin")
    if fetch.returncode != 0:
        print(f"git fetch failed: {fetch.stderr.strip()}")
        sys.exit(1)

    default_branch = get_default_branch()
    if not default_branch:
        print("Could not determine the default branch (no origin/main or origin/master found).")
        sys.exit(1)

    remote_ref = f"origin/{default_branch}"
    current_branch = get_current_branch()

    merged = run("branch", "--merged", remote_ref, "--format=%(refname:short)")
    candidates = [b for b in merged.stdout.splitlines() if b and b != default_branch and b != current_branch]

    if not candidates:
        print(f"No local branches to prune (nothing merged into {remote_ref} besides {default_branch}/current).")
        return

    print(f"Branches merged into {remote_ref}:")
    for b in candidates:
        print(f"  {b}")

    if not args.yes:
        print(f"\nDry run - nothing deleted. Re-run with --yes to actually delete these {len(candidates)} branch(es).")
        return

    for b in candidates:
        result = run("branch", "-d", b)
        if result.returncode == 0:
            print(f"Deleted {b}")
        else:
            print(f"Could not delete {b}: {result.stderr.strip()}")


if __name__ == "__main__":
    main()
