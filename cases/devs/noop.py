#! python3
# noop - does nothing and exits 0. Ignores any arguments.
# noop --fail - writes a message to stderr and exits 1.
#
# Exists purely to exercise `batch`'s success/failure paths against a real
# subprocess, not just mocks.

import sys

from core.stats import record_usage


def main(argv=None):
    record_usage("noop")
    args = sys.argv[1:] if argv is None else argv

    if "--fail" in args:
        print("noop: failing as requested", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
