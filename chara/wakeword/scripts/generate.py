"""Generate wakeword data through Chara and BrainBox."""

import argparse
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    from ..generation.pipeline import run
    from ..generation.settings import GenerationSettings

    try:
        result = run(GenerationSettings.read(args.config), args.output)
    except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
        print(
            f"Wakeword generation failed: {error}. Diagnostics: {args.output}",
            file=sys.stderr,
        )
        return 1
    return 0 if result.status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
