"""Rebuild an offline report from verified saved training measurements."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        from chara.wakeword.training.reporting import render_training_report

        print(render_training_report(args.output))
        return 0
    except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
        print(f"Report failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
