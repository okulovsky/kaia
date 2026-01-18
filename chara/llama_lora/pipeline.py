from chara.common import (
    CharaApis,
    ICache,
    BrainBoxCache,
    logger,
    BrainBoxUnit,
    DictCache,
)
from pathlib import Path
from brainbox.deciders.text.llama_lora_sft_trainer.api import TrainingSettings, TrainingRun
from brainbox import BrainBox
from brainbox.deciders import LlamaLoraSFTTrainer, LlamaLoraServer
from dataclasses import dataclass
from .stats import CheckpointValStats, TrainingRunStats, GenerationResult
from typing import Iterable
import json


@dataclass
class LoraTrainCase:
    adapter_name: str
    train_dataset: Path


@dataclass
class LoraGenerationCase:
    adapter_name: str
    inputs: list[str]
    expected_outputs: list[str]


class LlamaLoraCache(ICache[TrainingRunStats]):
    def __init__(self, working_folder: Path | None = None):
        super().__init__(working_folder)
        self.train_checkpoints = BrainBoxCache[LoraTrainCase, TrainingRun]()
        self.val_outputs = DictCache[BrainBoxCache[LoraGenerationCase, list[str]], None](
            BrainBoxCache
        )


class LlamaLoraPipeline:
    def __init__(
        self,
        model_id: str,
        settings: TrainingSettings | dict | None = None,
        val_batch_size: int = 64,
        max_tokens: int = 500,
    ):
        self.model_id = model_id
        self.settings = settings
        self.val_batch_size = val_batch_size
        self.max_tokens = max_tokens

    def _create_training_task(self, train_case: LoraTrainCase) -> BrainBox.ITask:
        return BrainBox.Task.call(LlamaLoraSFTTrainer).train(
            model_id=self.model_id,
            adapter_name=train_case.adapter_name,
            dataset=train_case.train_dataset,
            settings=self.settings,
        )

    def _create_generation_task(self, generation_case: LoraGenerationCase) -> BrainBox.ITask:
        return BrainBox.Task.call(LlamaLoraServer, self.model_id).completion(
            task_name=generation_case.adapter_name,
            prompts=generation_case.inputs,
            max_tokens=self.max_tokens,
        )

    @staticmethod
    def _get_generation_cases(
        adapter_name: str,
        val_dataset: Path,
        val_batch_size: int,
    ) -> Iterable[LoraGenerationCase]:
        def read_examples(f):
            for line in f:
                if not line.strip():
                    continue
                yield json.loads(line)

        with val_dataset.open("r") as f:
            batch_inputs = []
            batch_expected_outputs = []

            for example in read_examples(f):
                batch_inputs.append(example["INPUT"])
                batch_expected_outputs.append(example["OUTPUT"])
                if len(batch_inputs) == val_batch_size:
                    yield LoraGenerationCase(
                        adapter_name=adapter_name,
                        inputs=batch_inputs,
                        expected_outputs=batch_expected_outputs,
                    )
                    batch_inputs = []
                    batch_expected_outputs = []

            if batch_inputs:
                yield LoraGenerationCase(
                    adapter_name=adapter_name,
                    inputs=batch_inputs,
                    expected_outputs=batch_expected_outputs,
                )

    def __call__(
        self,
        cache: LlamaLoraCache,
        adapter_name: str,
        train_dataset: Path,
        val_dataset: Path,
    ):
        @logger.phase(cache.train_checkpoints, "Training a LoRA adapter")
        def _():
            unit = BrainBoxUnit(self._create_training_task)
            unit.run(
                cache.train_checkpoints,
                [LoraTrainCase(adapter_name=adapter_name, train_dataset=train_dataset)],
            )

        @logger.phase(cache.val_outputs, "Generating LLM responses on validation set")
        def _():
            training_run = cache.train_checkpoints.read_options().to_list()[0]
            gguf_checkpoints_dir = training_run.path / "gguf_checkpoints"
            gguf_checkpoints = list(gguf_checkpoints_dir.glob("checkpoint-*.gguf"))

            for index, gguf_checkpoint in enumerate(gguf_checkpoints):
                logger.log(f"Checkpoint {gguf_checkpoint}, {index}/{len(gguf_checkpoints)}")

                checkpoint_number = int(gguf_checkpoint.stem.split("-")[1])
                checkpoint_task_name = f"{training_run.guid}_{checkpoint_number}"
                checkpoint_adapter_dest = (
                    f"models/{self.model_id}/lora_adapters/{checkpoint_task_name}.gguf"
                )
                CharaApis.brainbox_api.controller_api.upload_resource(
                    "LlamaLoraServer", checkpoint_adapter_dest, gguf_checkpoint
                )

                subcache = cache.val_outputs.create_subcache(str(checkpoint_number))

                @logger.phase(subcache, f"Generating for checkpoint {checkpoint_number}")
                def _():
                    unit = BrainBoxUnit(self._create_generation_task)
                    unit.run(
                        subcache,
                        self._get_generation_cases(
                            adapter_name=checkpoint_task_name,
                            val_dataset=val_dataset,
                            val_batch_size=self.val_batch_size,
                        ),
                    )

                CharaApis.brainbox_api.controller_api.delete_resource(
                    "LlamaLoraServer", checkpoint_adapter_dest
                )
            cache.val_outputs.finalize()

        checkpoints_val_stats = []
        for checkpoint_number, subcache in cache.val_outputs.read_subcaches():
            generation_results = []
            for case, outputs in subcache.read_cases_and_options():
                for input_, expected_output, output in zip(
                    case.inputs, case.expected_outputs, outputs
                ):
                    generation_results.append(
                        GenerationResult(
                            input=input_,
                            expected_output=expected_output,
                            output=output,
                        )
                    )
            checkpoints_val_stats.append(
                CheckpointValStats(
                    number=int(checkpoint_number), generation_results=generation_results
                )
            )
        checkpoints_val_stats.sort(key=lambda x: x.number)

        cache.write_result(
            TrainingRunStats(
                training_run=cache.train_checkpoints.read_options().to_list()[0],
                checkpoints_val_stats=checkpoints_val_stats,
            )
        )
