#! python3
# prune-branches - delete branches already merged into origin's default
# branch (master/main). Dry-run by default.
#
# prune-branches                   list local branches that would be deleted
# prune-branches --yes             actually delete them
# prune-branches --remote          list origin branches that would be deleted
# prune-branches --remote --yes    actually delete them on origin

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


def prune_local(remote_ref, default_branch, do_delete):
    current_branch = get_current_branch()
    merged = run("branch", "--merged", remote_ref, "--format=%(refname:short)")
    candidates = [b for b in merged.stdout.splitlines() if b and b != default_branch and b != current_branch]

    if not candidates:
        print(f"No local branches to prune (nothing merged into {remote_ref} besides {default_branch}/current).")
        return

    print(f"Local branches merged into {remote_ref}:")
    for b in candidates:
        print(f"  {b}")

    if not do_delete:
        print(f"\nDry run - nothing deleted. Re-run with --yes to actually delete these {len(candidates)} branch(es).")
        return

    for b in candidates:
        result = run("branch", "-d", b)
        if result.returncode == 0:
            print(f"Deleted {b}")
        else:
            print(f"Could not delete {b}: {result.stderr.strip()}")


def prune_remote(remote_ref, default_branch, do_delete):
    default_remote_ref = f"origin/{default_branch}"
    merged = run("branch", "-r", "--merged", remote_ref, "--format=%(refname:short)")
    candidates = []
    for b in merged.stdout.splitlines():
        if not b or not b.startswith("origin/") or b == default_remote_ref:
            continue
        candidates.append(b[len("origin/") :])

    if not candidates:
        print(f"No remote branches to prune (nothing on origin merged into {remote_ref} besides {default_branch}).")
        return

    print(f"Remote branches (on origin) merged into {remote_ref}:")
    for b in candidates:
        print(f"  {b}")

    if not do_delete:
        print(
            f"\nDry run - nothing deleted. Re-run with --remote --yes to actually "
            f"delete these {len(candidates)} branch(es) on origin."
        )
        return

    for b in candidates:
        result = run("push", "origin", "--delete", b)
        if result.returncode == 0:
            print(f"Deleted origin/{b}")
        else:
            print(f"Could not delete origin/{b}: {result.stderr.strip()}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Delete branches already merged into origin's default branch")
    parser.add_argument("--yes", "-y", action="store_true", help="actually delete (default is a dry run)")
    parser.add_argument(
        "--remote",
        "-r",
        action="store_true",
        help="operate on origin's branches instead of local ones",
    )
    args = parser.parse_args(argv)

    if run("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("Not inside a git repository.")
        sys.exit(1)

    print("Fetching from origin...")
    fetch = run("fetch", "origin", "--prune")
    if fetch.returncode != 0:
        print(f"git fetch failed: {fetch.stderr.strip()}")
        sys.exit(1)

    default_branch = get_default_branch()
    if not default_branch:
        print("Could not determine the default branch (no origin/main or origin/master found).")
        sys.exit(1)

    remote_ref = f"origin/{default_branch}"

    if args.remote:
        prune_remote(remote_ref, default_branch, args.yes)
    else:
        prune_local(remote_ref, default_branch, args.yes)


if __name__ == "__main__":
    main()
