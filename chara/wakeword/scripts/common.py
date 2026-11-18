"""Python entry points replacing Make; handlers keep orchestration readable."""

import argparse
import os
from pathlib import Path


def parse_args(command, argv):
    parser = argparse.ArgumentParser(description="Wakeword " + command)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "learn-settings.json",
    )
    parser.add_argument(
        "--brainbox-url",
        default=os.environ.get("CHARA_BRAINBOX_URL", "http://127.0.0.1:8090"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=command in ("generate", "train", "report", "run"),
    )
    parser.add_argument("--dataset", type=Path, required=command == "train")
    parser.add_argument(
        "--scope", choices=("generation", "training", "all"), default="all"
    )
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args(argv)


def connect(args):
    from brainbox import BrainBox

    api = BrainBox.Api(args.brainbox_url)
    try:
        api.wait_for_connection(3)
    except Exception as error:
        raise RuntimeError(
            "BrainBox unavailable; start python -m brainbox.run --data-folder YOUR_SERVER_DATA_FOLDER on the server"
        ) from error
    return api


def generate(args):
    api = connect(args)
    from chara import Chara

    from ..generation.settings import GenerationSettings
    from ..generation_pipeline import generate_dataset

    Chara.Apis.brainbox_api = api
    return generate_dataset(GenerationSettings.read(args.config), args.output)


def train(args):
    from brainbox import BrainBox
    from brainbox.deciders.voice_analysis.wakeword_training.runtime.requirements import (
        requirements_from_config,
    )
    from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
        TrainingSettings,
    )
    from chara import Chara

    from ..training_pipeline import train_dataset

    Chara.Apis.brainbox_api = BrainBox.Api(args.brainbox_url)
    return train_dataset(
        args.dataset,
        TrainingSettings.read(args.config),
        requirements_from_config(args.config),
        args.output,
    )


def prepare(args):
    from ..environment import prepare_generation, prepare_training

    api = connect(args)
    if (
        args.scope in ("generation", "all")
        and not prepare_generation(api, args.config, args.check_only)["ready"]
    ):
        return {"status": "failed"}
    if args.scope in ("training", "all"):
        status = prepare_training(api, args.check_only)
        print(status)
        if not status["ready"]:
            return {"status": "failed"}
    return {"status": "complete"}


def full_run(args):
    from copy import copy

    root = args.output
    if args.dataset is None:
        generation_args = copy(args)
        generation_args.output = root / "generation"
        generate(generation_args)
        dataset = generation_args.output
    else:
        dataset = args.dataset
    training_args = copy(args)
    training_args.dataset = dataset
    training_args.output = root / "training"
    return train(training_args)


def report(args):
    from brainbox.deciders.voice_analysis.wakeword_training.runtime.reporting import (
        render_training_report,
    )

    print(render_training_report(args.output))
    return {"status": "complete"}


def main(command, argv=None):
    args = parse_args(command, argv)
    os.environ["CHARA_BRAINBOX_URL"] = args.brainbox_url
    try:
        result = {
            "generate": generate,
            "run": full_run,
            "train": train,
            "prepare": prepare,
            "report": report,
        }[command](args)
        status = result["status"] if isinstance(result, dict) else result.status
        print(
            f"{command}: {status}"
            + (f"; {args.output.resolve()}" if args.output else "")
        )
        return 0 if status == "complete" else 1
    except Exception as error:  # noqa: BLE001 - CLI reports failures without false success.
        print(f"{command} failed: {error}")
        return 1
