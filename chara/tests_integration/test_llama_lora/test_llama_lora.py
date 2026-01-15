from chara.common import logger, CharaApis
from chara.llama_lora.pipeline import (
    LlamaLoraPipeline,
    TrainingSettings,
    LlamaLoraCache,
)
from chara.llama_lora.stats import CheckpointValStats
from brainbox import BrainBox
from unittest import TestCase
from foundation_kaia.misc import Loc
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from itertools import chain


def plot_accuracy_by_checkpoint(checkpoints_val_stats):
    xs = [c.number for c in checkpoints_val_stats]
    ys = [c.get_accuracy() for c in checkpoints_val_stats]

    fig, ax = plt.subplots()
    ax.plot(xs, ys, marker="o")
    ax.set_xlabel("Checkpoint")
    ax.set_ylabel("Accuracy")
    ax.set_title("Validation accuracy by checkpoint")
    ax.grid(True)
    return fig


def plot_train_stats(train_stats):
    df = pd.DataFrame(
        [
            {
                "step": s.step,
                "loss": s.loss,
                "grad_norm": s.grad_norm,
                "learning_rate": s.learning_rate,
            }
            for s in train_stats
        ]
    )
    figures = []

    for col in ["loss", "grad_norm", "learning_rate"]:
        fig, ax = plt.subplots()
        ax.plot(df["step"], df[col])
        ax.set_xlabel("Step")
        ax.set_ylabel(col)
        ax.set_title(f"Train {col} by step")
        ax.grid(True)
        figures.append(fig)

    return figures


def log_checkpoint_stats(logger, checkpoint: CheckpointValStats):
    acc = checkpoint.get_accuracy()
    wrong = checkpoint.get_wrong_predictions()

    logger.log(f"Accuracy: {acc:.4f}")

    if not wrong:
        logger.log("No wrong predictions")
    else:
        df = pd.DataFrame(
            [
                {
                    "input": r.input,
                    "expected": r.expected_output,
                    "output": r.output,
                }
                for r in wrong
            ]
        )

        logger.log(df)


def run_llama_lora_test(
    *,
    model_id: str,
    settings: TrainingSettings,
    val_batch_size: int,
    max_tokens: int,
    adapter_name: str,
    train_dataset: Path,
    val_dataset: Path,
):
    with Loc.create_test_folder() as working_folder:
        with BrainBox.Api.Test() as api:
            CharaApis.brainbox_api = api
            cache = LlamaLoraCache(working_folder)
            pipeline = LlamaLoraPipeline(
                model_id=model_id,
                settings=settings,
                val_batch_size=val_batch_size,
                max_tokens=max_tokens,
            )
            pipeline(
                cache=cache,
                adapter_name=adapter_name,
                train_dataset=train_dataset,
                val_dataset=val_dataset,
            )

        stats = cache.read_result()

    with logger.html_report(Path(__file__).parent / f"{adapter_name}_lora_stats.html"):
        with logger.section("Summary"):
            logger.log(f"Model: {model_id}")
            logger.log(f"Adapter: {adapter_name}")
            logger.log(f"Checkpoints evaluated: {len(stats.checkpoints_val_stats)}")

        with logger.section("Checkpoint details"):
            for checkpoint in stats.checkpoints_val_stats:
                with logger.section(f"Checkpoint {checkpoint.number}"):
                    log_checkpoint_stats(logger, checkpoint)

        with logger.section("Plots"):
            for fig in chain(
                plot_train_stats(stats.train_stats),
                [plot_accuracy_by_checkpoint(stats.checkpoints_val_stats)],
            ):
                logger.log(fig)


class LlamaLoraTestCase(TestCase):
    def test_01_llama_lora_report(self):
        model_id = "gemma-3-270m-it"

        settings = TrainingSettings(
            training_args={
                "num_train_epochs": 1.0,
                "per_device_train_batch_size": 2,
                "gradient_accumulation_steps": 1,
                "learning_rate": 2e-4,
                "logging_steps": 1,
                "save_strategy": "steps",
                "save_steps": 0.02,
                "save_total_limit": 3,
                "report_to": "none",
                "weight_decay": 0.01,
                "lr_scheduler_type": "cosine",
                "warmup_ratio": 0.1,
                "seed": 252,
                "fp16": True,
            },
        )

        run_llama_lora_test(
            model_id=model_id,
            settings=settings,
            val_batch_size=2,
            max_tokens=10,
            adapter_name="food_skill_small",
            train_dataset=Path(__file__).parent / "small_train_example.jsonl",
            val_dataset=Path(__file__).parent / "small_val_example.jsonl",
        )

    def test_02_llama_lora_full(self):
        model_id = "gemma-3-270m-it"

        settings = TrainingSettings(
            training_args={
                "num_train_epochs": 5.0,
                "per_device_train_batch_size": 16,
                "gradient_accumulation_steps": 1,
                "learning_rate": 2e-4,
                "logging_steps": 10,
                "save_strategy": "steps",
                "save_steps": 0.02,
                "save_total_limit": 100,
                "report_to": "none",
                "weight_decay": 0.01,
                "lr_scheduler_type": "cosine",
                "warmup_ratio": 0.1,
                "seed": 252,
                "fp16": True,
            },
        )

        run_llama_lora_test(
            model_id=model_id,
            settings=settings,
            val_batch_size=64,
            max_tokens=500,
            adapter_name="food_skill_full",
            train_dataset=Path(__file__).parent / "train_example.jsonl",
            val_dataset=Path(__file__).parent / "val_example.jsonl",
        )
