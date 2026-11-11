"""Scope-aware generation/training commands."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _generation(args, command):
    values = [
        command,
        "--brainbox-url",
        args.brainbox_url,
        "--config",
        str(args.config),
    ]
    if args.output:
        values += ["--output", str(args.output)]
    return subprocess.run(
        [sys.executable, str(PACKAGE / "scripts/generation_manage.py"), *values],
        check=False,
    ).returncode


def _training_preflight(args):
    from chara.wakeword.training.dependencies import issues, resolve_device
    from chara.wakeword.training.inputs import resolve_inputs
    from chara.wakeword.training.settings import TrainingSettings

    settings = TrainingSettings.read(args.training_config)
    problems = issues()
    if problems:
        raise ValueError("; ".join(problems) + ". Run make setup SCOPE=training")
    resolve_device(settings.device)
    if args.dataset:
        _, arrays = resolve_inputs(args.dataset)
        for array in arrays.values():
            if not array._mmap.closed:
                array._mmap.close()
    print("READY    training/dependencies              local CPU/export/report stack")
    if args.dataset:
        print(
            "READY    training/inputs                    hashes, shapes, provenance, segmentation"
        )


def _setup_training():
    code = "import sys; sys.path.insert(0,sys.argv[1]); from chara.wakeword.training.dependencies import issues; p=issues(); print(p); sys.exit(10 if p else 0)"
    preflight = subprocess.run([sys.executable, "-c", code, str(ROOT)], check=False)
    if preflight.returncode not in (0, 10):
        raise RuntimeError("training setup preflight failed")
    if preflight.returncode == 10:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--prefer-binary",
                "-r",
                str(PACKAGE / "requirements-host.lock.txt"),
            ],
            check=True,
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("check", "setup", "run", "generate", "train", "report")
    )
    parser.add_argument(
        "--brainbox-url",
        default=os.environ.get("CHARA_BRAINBOX_URL", "http://127.0.0.1:8090"),
    )
    parser.add_argument("--config", type=Path, default=PACKAGE / "learn-settings.json")
    parser.add_argument("--training-config", type=Path)
    parser.add_argument(
        "--scope", choices=("generation", "training", "full"), default="full"
    )
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    args.training_config = args.training_config or args.config
    if args.command in ("run", "generate", "train", "report") and args.output is None:
        parser.error("operation requires --output")
    if args.command == "train" and args.dataset is None:
        parser.error("train requires --dataset")
    os.environ["CHARA_BRAINBOX_URL"] = args.brainbox_url
    try:
        if args.command == "report":
            from chara.wakeword.training.reporting import render_training_report

            print(render_training_report(args.output))
            return 0
        if args.command == "generate":
            return _generation(args, "run")
        generation_scope = args.scope in ("generation", "full") and not (
            args.scope == "full" and args.dataset
        )
        training_scope = args.scope in ("training", "full")
        if args.command in ("check", "setup"):
            if args.command == "setup" and training_scope:
                _setup_training()
            if generation_scope:
                code = _generation(args, args.command)
                if code:
                    return code
            if training_scope:
                _training_preflight(args)
            return 0
        from chara.wakeword.training.settings import TrainingSettings

        settings = TrainingSettings.read(args.training_config)
        if args.command == "train":
            from chara.wakeword.training.pipeline import run_training

            result = run_training(args.dataset, settings, args.output)
        else:
            from chara.wakeword import GenerationSettings
            from chara.wakeword.training.full_pipeline import run_full

            generation = None if args.dataset else GenerationSettings.read(args.config)
            cached = (args.output / "full-run.json").is_file()
            if not args.dataset and not cached and _generation(args, "check"):
                print(
                    "Not ready. Run make setup with the same parameters.",
                    file=sys.stderr,
                )
                return 1
            result = run_full(generation, settings, args.output, args.dataset)
        if result.status != "complete":
            raise RuntimeError(result.error)
        print(f"{args.command}: complete; {args.output.resolve()}")
        return 0
    except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
