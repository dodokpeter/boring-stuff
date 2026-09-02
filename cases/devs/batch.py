#! python3
# batch - run a queued list of commands from <cloud.folder>/toProcess.txt,
# one at a time, sequentially (the next command starts only after the
# previous one has fully exited - no parallelism, no background spawning).
# Each command's line is removed from the queue as it completes (success or
# failure), so a re-run picks up where the last one stopped rather than
# re-running everything.
#
# batch             run the queue
# batch --dry-run   list what would run, without touching anything -
#                   no execution, no queue rewrite, no log files
#
# Blank lines and lines starting with "#" are skipped, so the queue file
# can carry comments/spacing. A failing command is logged and the run
# continues with the next line - it does not stop the batch.
#
# Logging, per calendar day, in <cloud.folder>/logs/ (created if missing,
# always appended to, never truncated):
#   <yyyy-mm-dd>_processed.txt      one line per command that exited 0
#   <yyyy-mm-dd>_errors.txt         one line per command that failed
#                                   (verbatim, so it can be renamed to
#                                   toProcess.txt to retry just the
#                                   failures)
#   <yyyy-mm-dd>_errors_logs.txt    a diagnostics block per failed command
#                                   (timestamp, command, exit code, stderr,
#                                   and stdout when non-empty) - nothing is
#                                   written here for successful commands
#
# Configuration: uses the same cloud.folder as move-to/shared-drive/yt -c
# (core/cloud.py) - no separate config of its own.

import argparse
import subprocess
import sys
import time
from datetime import datetime

from core.cloud import load_cloud_folder
from core.configuration.user_conf import MissingConfigError
from core.stats import record_usage

QUEUE_FILE_NAME = "toProcess.txt"
LOGS_FOLDER_NAME = "logs"


def read_queue(queue_path):
    """Return the pending command lines from queue_path (blank lines and
    lines starting with "#" already dropped), or None if the file doesn't
    exist."""
    if not queue_path.is_file():
        return None

    lines = []
    for raw_line in queue_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def write_queue(queue_path, lines):
    """Atomically rewrite queue_path with `lines` - written to a temp file
    in the same directory, then moved into place with os.replace (atomic
    on Windows for a same-volume move), so a crash mid-write leaves either
    the old or the new content, never a truncated file.

    The move itself is retried a few times on PermissionError - on Windows
    it can transiently fail (antivirus/indexer briefly holding the
    just-written temp file) even though nothing is actually wrong; this
    has been observed for real, not just theorized."""
    tmp_path = queue_path.with_suffix(queue_path.suffix + ".tmp")
    tmp_path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")

    attempts = 5
    for attempt in range(1, attempts + 1):
        try:
            tmp_path.replace(queue_path)
            return
        except PermissionError:
            if attempt == attempts:
                raise
            time.sleep(0.05)


def log_paths(logs_dir, date_str):
    return {
        "processed": logs_dir / f"{date_str}_processed.txt",
        "errors": logs_dir / f"{date_str}_errors.txt",
        "errors_logs": logs_dir / f"{date_str}_errors_logs.txt",
    }


def append_line(path, line):
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{line}\n")


def append_error_diagnostics(path, line, result, timestamp):
    parts = [f"[{timestamp}] {line}", f"exit code: {result.returncode}", "stderr:", result.stderr or "(empty)"]
    if result.stdout:
        parts.append("stdout:")
        parts.append(result.stdout)
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n\n")


def run_command_line(line):
    """Run one queue line through the shell (so it can use pipes,
    redirects, and quoted Windows paths the way it would if typed
    directly), capturing its output rather than streaming it."""
    return subprocess.run(line, shell=True, capture_output=True, text=True)


def process_queue_file(cloud_folder, dry_run=False):
    """Run the queue at <cloud_folder>/toProcess.txt. Returns a process
    exit code (0 on success, including "nothing to do")."""
    queue_path = cloud_folder / QUEUE_FILE_NAME
    lines = read_queue(queue_path)

    if lines is None:
        print(f"No queue file found at {queue_path}")
        return 1

    if not lines:
        print("Nothing to do - toProcess.txt has no pending commands.")
        return 0

    if dry_run:
        print("Would run, in order:")
        for line in lines:
            print(f"  {line}")
        return 0

    logs_dir = cloud_folder / LOGS_FOLDER_NAME
    logs_dir.mkdir(parents=True, exist_ok=True)

    remaining = list(lines)
    for line in lines:
        print(f"Running: {line}")
        result = run_command_line(line)

        now = datetime.now()
        remaining.pop(0)
        write_queue(queue_path, remaining)

        paths = log_paths(logs_dir, now.strftime("%Y-%m-%d"))
        if result.returncode == 0:
            print("  ok (exit 0)")
            append_line(paths["processed"], line)
        else:
            print(f"  failed (exit {result.returncode})")
            append_line(paths["errors"], line)
            append_error_diagnostics(paths["errors_logs"], line, result, now.strftime("%Y-%m-%d %H:%M:%S"))

    return 0


def main(argv=None):
    record_usage("batch")
    parser = argparse.ArgumentParser(description="Run a queued list of commands from the cloud folder")
    parser.add_argument("--dry-run", action="store_true", help="list what would run, without touching anything")
    args = parser.parse_args(argv)

    try:
        cloud_folder = load_cloud_folder()
    except MissingConfigError as e:
        print(e)
        sys.exit(1)

    if not cloud_folder.is_dir():
        print(f"Configured cloud folder is not accessible: {cloud_folder}")
        sys.exit(1)

    sys.exit(process_queue_file(cloud_folder, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
