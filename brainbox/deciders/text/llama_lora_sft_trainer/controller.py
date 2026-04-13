import json
from unittest import TestCase
from ....framework import (
    BrainboxImageBuilder,
    IImageBuilder,
    BrainBoxApi,
    BrainBoxTask,
    DockerMarshallingController,
    RunConfiguration,
)
from foundation_kaia.marshalling import TypeTools
from .app.interface import TrainingRun
from .settings import LlamaLoraSFTTrainerSettings
from pathlib import Path


class LlamaLoraSFTTrainerController(DockerMarshallingController[LlamaLoraSFTTrainerSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            "3.13.2",
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            ),
            repository=BrainboxImageBuilder.Repository(
                url="https://github.com/ggml-org/llama.cpp",
                commit="dd62dcfab97e420949519fd0eac9fca7bf97e635",
                install=True,
                pip_install_options="",
                path_to_package="./gguf-py",
                remove_repo=True,
            ),
            keep_dockerfile=True,
        )

    def get_default_settings(self):
        return LlamaLoraSFTTrainerSettings()

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            set_env_variables={"HF_HOME": "/resources/models"},
        )

    def create_api(self):
        from .api import LlamaLoraSFTTrainerApi
        return LlamaLoraSFTTrainerApi()

    def custom_self_test(self, api: BrainBoxApi, tc: TestCase):
        from .api import LlamaLoraSFTTrainer
        from ..llama_lora_server import LlamaLoraServer

        model_id = "gemma-3-270m-it"
        adapter_name = "timer_skill"
        timer_dataset = Path(__file__).parent / "train_example.jsonl"
        training_settings = LlamaLoraSFTTrainer.TrainingSettings(
            training_args={
                "num_train_epochs": 0.7,
                "per_device_train_batch_size": 8,
                "gradient_accumulation_steps": 2,
                "learning_rate": 2e-4,
                "logging_steps": 10,
                "save_strategy": "steps",
                "save_steps": 0.02,
                "save_total_limit": 1,
                "report_to": "none",
                "weight_decay": 0.01,
                "lr_scheduler_type": "cosine",
                "warmup_ratio": 0.1,
                "seed": 252,
                "fp16": True,
            },
        )

        task = LlamaLoraSFTTrainer.new_task().train(
            model_id, adapter_name, training_settings, timer_dataset
        )

        id = None
        try:
            id = api.add(task)
            log_file = api.join(id)
        except Exception:
            if id is not None:
                from pprint import pprint
                pprint(api.tasks.get_log(id))
            raise

        training_run = None
        lines = api.cache.read_file(log_file).string_content.split('\n')
        for line in lines:
            if len(line.strip()) > 0:
                js = json.loads(line)
                if js['result'] is not None:
                    training_run = TypeTools.deserialize(js['result'], TrainingRun)

        tc.assertIsNotNone(training_run)
        tc.assertIsInstance(training_run, TrainingRun)

        run_path = self.resource_folder("experiments", model_id, adapter_name, training_run.guid)
        tc.assertTrue(run_path.exists())
        for item in ["settings.json", "train.jsonl", "hf_checkpoints", "gguf_checkpoints"]:
            tc.assertTrue((run_path / item).exists())

        gguf_checkpoints_dir = run_path / "gguf_checkpoints"
        gguf_files = list(gguf_checkpoints_dir.glob("checkpoint-*.gguf"))
        tc.assertTrue(len(gguf_files) > 0, "No GGUF checkpoint files found")
        tc.assertEqual(
            len(gguf_files),
            len(list(gguf_checkpoints_dir.iterdir())),
            "Directory contains non-GGUF files",
        )

        latest_gguf_checkpoint = max(gguf_files, key=lambda f: int(f.stem.split("-")[1]))
        temporary_task_name = training_run.guid
        temporary_adapter_dest = f"models/{model_id}/lora_adapters/{temporary_task_name}.gguf"
        api.resources(LlamaLoraServer).upload(temporary_adapter_dest, latest_gguf_checkpoint)

        timer_prompt = "USER:set a timer for 5 seconds\n"
        timer_task_result = api.execute(
            LlamaLoraServer.new_task(parameter=model_id).completion(
                task_name=temporary_task_name, prompt=timer_prompt
            )
        )
        tc.assertEqual(timer_task_result, "HOURS:0\nMINUTES:0\nSECONDS:5")

        api.resources(LlamaLoraServer).delete(temporary_adapter_dest)
