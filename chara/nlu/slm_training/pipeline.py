import json
from pathlib import Path
from brainbox import BrainBox
from brainbox.framework import ControllerRegistry
from brainbox.deciders import LlamaLoraSFTTrainer, LlamaLoraServer
from brainbox.deciders.text.llama_lora_sft_trainer.api import TrainingSettings, TrainingRun
from foundation_kaia.marshalling import TypeTools
from chara.common import Chara, logger, brainbox_training_pipeline
from .stats import CheckpointValStats, TrainingRunStats, GenerationResult, TrainStats


def training_run_folder(run: TrainingRun) -> str:
    """The folder of the run in the resources of LlamaLoraSFTTrainer"""
    return f'experiments/{run.model_id}/{run.adapter_name}/{run.guid}'


def checkpoint_numbers(run: TrainingRun) -> list[int]:
    files = Chara.Apis.brainbox_api.resources(LlamaLoraSFTTrainer).list(f'{training_run_folder(run)}/gguf_checkpoints', suffix='.gguf')
    return sorted(int(Path(f).stem.split('-')[1]) for f in files)


def upload_checkpoint(run: TrainingRun, number: int, task_name: str) -> str:
    """Uploads the checkpoint to LlamaLoraServer as the adapter `task_name` and restarts the server to load it."""
    api = Chara.Apis.brainbox_api
    destination = f'models/{run.model_id}/lora_adapters/{task_name}.gguf'
    source = f'{training_run_folder(run)}/gguf_checkpoints/checkpoint-{number}.gguf'
    api.resources(LlamaLoraServer).upload(destination, api.resources(LlamaLoraSFTTrainer).open(source))
    restart_llama_lora_server()
    return destination


def restart_llama_lora_server():
    # LlamaLoraServer loads the adapters at the start, so the running instances must be stopped to see the new ones
    api = Chara.Apis.brainbox_api
    name = ControllerRegistry.to_controller_name(LlamaLoraServer)
    for controller in api.controllers.status().controllers:
        if controller.name == name:
            for instance in controller.instances:
                api.controllers.stop(controller.name, instance.instance_id)


class LlamaLoraPipeline:
    """
    Trains a LoRA adapter with LlamaLoraSFTTrainer and validates every checkpoint of the run on LlamaLoraServer.
    Datasets are jsonl files with `INPUT` and `OUTPUT` fields.
    """
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

    def _create_training_task(self, adapter_name: str, train_dataset: Path) -> BrainBox.Task:
        return LlamaLoraSFTTrainer.new_task().train(
            model_id=self.model_id,
            adapter_name=adapter_name,
            dataset=train_dataset,
            settings=self.settings,
        )

    def __call__(self, adapter_name: str, train_dataset: Path, val_dataset: Path) -> TrainingRunStats:
        result = Chara.call(brainbox_training_pipeline)(self._create_training_task(adapter_name, train_dataset))
        run = TypeTools.deserialize(result, TrainingRun) if isinstance(result, dict) else result

        @Chara.phase
        def checkpoints():
            return checkpoint_numbers(run)

        @Chara.phase
        def train_stats():
            return self._read_train_stats(run, checkpoints)

        examples = [json.loads(line) for line in val_dataset.read_text().splitlines() if line.strip()]
        checkpoints_val_stats = []
        for index, number in enumerate(checkpoints):
            logger.info(f"Checkpoint {number}, {index + 1}/{len(checkpoints)}")
            checkpoints_val_stats.append(
                Chara.call(self._validate_checkpoint, f'checkpoint_{number}')(run, number, examples)
            )
        return TrainingRunStats(run, checkpoints_val_stats, train_stats)

    def _read_train_stats(self, run: TrainingRun, numbers: list[int]) -> list[TrainStats]:
        if len(numbers) == 0:
            return []
        state = f'{training_run_folder(run)}/hf_checkpoints/checkpoint-{numbers[-1]}/trainer_state.json'
        storage = Chara.Apis.brainbox_api.resources(LlamaLoraSFTTrainer)
        if not storage.is_file(state):
            return []
        return TrainStats.from_trainer_state(json.loads(storage.read(state)))

    def _validate_checkpoint(self, run: TrainingRun, number: int, examples: list[dict]) -> CheckpointValStats:
        task_name = f'{run.guid}_{number}'
        destination = upload_checkpoint(run, number, task_name)
        try:
            outputs = []
            for start in range(0, len(examples), self.val_batch_size):
                batch = [e['INPUT'] for e in examples[start:start + self.val_batch_size]]
                outputs.extend(Chara.Apis.brainbox_api.execute(
                    LlamaLoraServer.new_task(parameter=self.model_id).completion(
                        task_name=task_name, prompts=batch, max_tokens=self.max_tokens,
                    )
                ))
        finally:
            Chara.Apis.brainbox_api.resources(LlamaLoraServer).delete(destination)
        return CheckpointValStats(
            number=number,
            generation_results=[
                GenerationResult(input=e['INPUT'], expected_output=e['OUTPUT'], output=output)
                for e, output in zip(examples, outputs)
            ],
        )
