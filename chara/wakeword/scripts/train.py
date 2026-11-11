"""Train a wakeword classifier on a ready dataset, export ONNX and report."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--background-manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        from chara.wakeword.training.pipeline import run_training
        from chara.wakeword.training.settings import TrainingSettings

        result = run_training(
            args.dataset,
            TrainingSettings.read(args.config),
            args.output,
            args.background_manifest,
        )
        if result.status != "complete":
            print(
                f"Training failed [{result.error_stage}]: {result.error}",
                file=sys.stderr,
            )
            return 1
        print(f"Training complete\nONNX: {result.model}\nReport: {result.report}")
        return 0
    except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
        print(f"Training failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
