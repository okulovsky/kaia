"""Deprecated Python command aliases for independent BrainBox pipelines."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    from chara.wakeword.scripts.common import main as canonical_main

    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        raise SystemExit("Use prepare, generate, train or report")
    command = args.pop(0)
    if command in ("check", "setup"):
        if command == "check":
            args.append("--check-only")
        command = "prepare"
    args = [("all" if item == "full" else item) for item in args]
    return canonical_main(command, args)


if __name__ == "__main__":
    raise SystemExit(main())
