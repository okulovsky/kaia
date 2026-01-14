from chara.common import CharaApis
from unittest import TestCase
from brainbox.deciders import Mock, Collector
from brainbox import BrainBox
from brainbox.framework import FileLike
from foundation_kaia.misc import Loc
from typing import Optional
from chara.llama_lora.pipeline import (
    LlamaLoraPipeline,
    TrainingSettings,
    LlamaLoraCache,
    TrainingRun,
)
from chara.llama_lora.stats import TrainStats, GenerationResult
from pathlib import Path
import shutil


class LlamaLoraSFTTrainerMock(Mock):
    def __init__(self, training_run_folder: Path):
        super().__init__("LlamaLoraSFTTrainer")
        self.training_run_folder = training_run_folder

    def train(
        self,
        model_id: str,
        adapter_name: str,
        dataset: FileLike.Type,
        settings: TrainingSettings | dict | None = None,
    ) -> TrainingRun:
        gguf_dir = self.training_run_folder / "gguf_checkpoints"
        gguf_dir.mkdir()
        checkpoint_numbers = [5, 10, 13]
        for checkpoint_number in checkpoint_numbers:
            (self.training_run_folder / "hf_checkpoints" / f"checkpoint-{checkpoint_number}").mkdir(
                parents=True
            )
            gguf_path = gguf_dir / f"checkpoint-{checkpoint_number}.gguf"
            gguf_path.touch()

        trainer_state = Path(__file__).parent / "mock_trainer_state.json"
        shutil.copy(
            trainer_state,
            self.training_run_folder
            / "hf_checkpoints"
            / f"checkpoint-{checkpoint_numbers[-1]}"
            / "trainer_state.json",
        )

        return TrainingRun(
            model_id=model_id,
            adapter_name=adapter_name,
            guid="goat_guid",
            path=self.training_run_folder,
        )


class LlamaLoraServerMock(Mock):
    def __init__(self):
        super().__init__("LlamaLoraServer")

    def completion(
        self,
        *,
        task_name: str,
        prompts: Optional[list[str]] = None,
        max_tokens: int = 500,
    ) -> str | list[str]:
        return [f"goat_output{prompt[-1]}" for prompt in prompts]


class LlamaLoraPipelineTestCase(TestCase):
    def test_mocked_pipeline(self):
        model_id = "goat_model"
        adapter_name = "goat_skill"
        val_batch_size = 2
        train_dataset = Path(__file__).parent / "mock_train_example.jsonl"
        val_dataset = Path(__file__).parent / "mock_val_example.jsonl"

        with (
            Loc.create_test_folder(dont_delete=True) as working_folder,
            Loc.create_test_folder(dont_delete=True) as training_run_folder,
        ):
            with BrainBox.Api.Test(
                [LlamaLoraServerMock(), LlamaLoraSFTTrainerMock(training_run_folder), Collector()]
            ) as api:
                CharaApis.brainbox_api = api
                cache = LlamaLoraCache(working_folder)
                pipeline = LlamaLoraPipeline(
                    model_id=model_id,
                    val_batch_size=val_batch_size,
                )
                pipeline(
                    cache=cache,
                    adapter_name=adapter_name,
                    train_dataset=train_dataset,
                    val_dataset=val_dataset,
                )

            stats = cache.read_result()

            self.assertEqual(stats.training_run.model_id, model_id)
            self.assertEqual(stats.training_run.adapter_name, adapter_name)
            self.assertEqual(stats.training_run.guid, "goat_guid")
            self.assertEqual(stats.training_run.path, training_run_folder)

            self.assertEqual(
                stats.train_stats,
                [
                    TrainStats(step=5, loss=2.5, learning_rate=0.0002, grad_norm=8.1),
                    TrainStats(step=10, loss=1.5, learning_rate=0.0001, grad_norm=3.1),
                ],
            )

            self.assertEqual(len(stats.checkpoints_val_stats), 3)
            for number, checkpoint_val_stats in zip([5, 10, 13], stats.checkpoints_val_stats):
                self.assertEqual(checkpoint_val_stats.number, number)
                self.assertEqual(len(checkpoint_val_stats.generation_results), 5)
                for i, generation_result in enumerate(
                    checkpoint_val_stats.generation_results, start=1
                ):
                    if i != 3:
                        self.assertEqual(generation_result.input, f"goat_input{i}")
                        self.assertEqual(generation_result.expected_output, f"goat_output{i}")
                        self.assertEqual(generation_result.output, f"goat_output{i}")
                    else:
                        self.assertEqual(generation_result.input, f"bad_input{i}")
                        self.assertEqual(generation_result.expected_output, f"bad_output{i}")
                        self.assertEqual(generation_result.output, f"goat_output{i}")
                self.assertEqual(checkpoint_val_stats.get_accuracy(), 0.8)
                wrong_predictions = checkpoint_val_stats.get_wrong_predictions()
                self.assertEqual(len(wrong_predictions), 1)
                self.assertEqual(
                    wrong_predictions[0],
                    GenerationResult(
                        input="bad_input3",
                        expected_output="bad_output3",
                        output="goat_output3",
                    ),
                )
