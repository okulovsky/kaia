import json
from pathlib import Path
from typing import Optional
from unittest import TestCase
from unittest.mock import patch
from brainbox import BrainBox, File, ISelfManagingDecider
from brainbox.deciders import Collector, LlamaLoraSFTTrainer
from foundation_kaia.marshalling import FileLike, TypeTools
from foundation_kaia.misc import Loc
from chara.common import Chara
from chara.nlu.slm_training.pipeline import LlamaLoraPipeline, TrainingRun
from chara.nlu.slm_training.stats import TrainStats, GenerationResult

FOLDER = Path(__file__).parent
CHECKPOINTS = (5, 10, 13)


class LlamaLoraSFTTrainerMock(ISelfManagingDecider):
    def __init__(self):
        self.trainings = 0

    def get_name(self):
        return "LlamaLoraSFTTrainer"

    def train(self, model_id: str, adapter_name: str, settings=None, dataset: FileLike = None) -> File:
        # The real service streams report items, which BrainBox stores as a jsonl file in the cache
        self.trainings += 1
        run = TrainingRun(model_id=model_id, adapter_name=adapter_name, guid="mock_guid")
        lines = [dict(log='training', progress=None, result=None), dict(log=None, progress=1, result=TypeTools.serialize(run, TrainingRun))]
        return File('training-report.jsonl', '\n'.join(json.dumps(line) for line in lines))


class LlamaLoraServerMock(ISelfManagingDecider):
    def __init__(self):
        self.task_names = []

    def get_name(self):
        return "LlamaLoraServer"

    def completion(self, *, task_name: str, prompt: Optional[str] = None, prompts: Optional[list[str]] = None, max_tokens: int = 500) -> str | list[str]:
        self.task_names.append(task_name)
        return [f"\noutput{p[-1]}\n" for p in prompts]


def _upload_run_files(api, model_id: str, adapter_name: str):
    run = f'experiments/{model_id}/{adapter_name}/mock_guid'
    storage = api.resources(LlamaLoraSFTTrainer)
    for number in CHECKPOINTS:
        storage.upload(f'{run}/gguf_checkpoints/checkpoint-{number}.gguf', b'gguf')
    storage.upload(f'{run}/hf_checkpoints/checkpoint-{CHECKPOINTS[-1]}/trainer_state.json', (FOLDER / 'mock_trainer_state.json').read_bytes())


class LlamaLoraPipelineTestCase(TestCase):
    def test_mocked_pipeline(self):
        model_id = "mock_pipeline_model"
        adapter_name = "mock_skill"
        trainer, server = LlamaLoraSFTTrainerMock(), LlamaLoraServerMock()

        # Restarting the server needs the controllers' status, which asks Docker
        with Loc.create_test_folder() as folder, patch('chara.nlu.slm_training.pipeline.restart_llama_lora_server') as restart:
            with BrainBox.Api.serverless_test([server, trainer, Collector()]) as api:
                Chara.Apis.brainbox_api = api
                _upload_run_files(api, model_id, adapter_name)
                pipeline = LlamaLoraPipeline(model_id=model_id, val_batch_size=2)
                for _ in range(2):  # the second run is restored from the cache
                    Chara.start(folder)
                    stats = Chara.call(pipeline)(adapter_name, FOLDER / "mock_train_example.jsonl", FOLDER / "mock_val_example.jsonl")
                temporary_adapters = api.resources('LlamaLoraServer').list(f'models/{model_id}/lora_adapters')

        self.assertEqual(1, trainer.trainings)
        self.assertEqual(len(CHECKPOINTS), restart.call_count)
        self.assertEqual({f'mock_guid_{n}' for n in CHECKPOINTS}, set(server.task_names))
        self.assertEqual([], temporary_adapters)

        self.assertEqual(TrainingRun(model_id, adapter_name, "mock_guid"), stats.training_run)
        self.assertEqual(
            [TrainStats(step=5, loss=2.5, learning_rate=0.0002, grad_norm=8.1),
             TrainStats(step=10, loss=1.5, learning_rate=0.0001, grad_norm=3.1)],
            stats.train_stats,
        )
        self.assertEqual(list(CHECKPOINTS), [c.number for c in stats.checkpoints_val_stats])
        for checkpoint in stats.checkpoints_val_stats:
            self.assertEqual(5, len(checkpoint.generation_results))
            self.assertEqual(0.8, checkpoint.get_accuracy())
            self.assertEqual(
                [GenerationResult(input="bad_input3", expected_output="bad_output3", output="\noutput3\n")],
                checkpoint.get_wrong_predictions(),
            )
        self.assertEqual(CHECKPOINTS[-1], stats.get_best_checkpoint().number)
