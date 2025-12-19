from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration,
    TestReport,
    BrainboxImageBuilder,
    IImageBuilder,
    BrainBoxApi,
    BrainBoxTask,
    OnDemandDockerController,
)
from .settings import LlamaLoraSFTTrainerSettings
from pathlib import Path
import shutil
import os


class LlamaLoraSFTTrainerController(OnDemandDockerController[LlamaLoraSFTTrainerSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent / "container",
            "3.13.2",
            allow_arm64=True,
            custom_dependencies=(BrainboxImageBuilder.Dependencies(),),
            repository=BrainboxImageBuilder.Repository(
                url="https://github.com/ggml-org/llama.cpp",
                commit="dd62dcfab97e420949519fd0eac9fca7bf97e635",
                install=True,
                pip_install_options="--user",
                path_to_package="./gguf-py",
                remove_repo=True,
            ),
            keep_dockerfile=True,
        )

    def get_base_configuration(self) -> RunConfiguration:
        return RunConfiguration(
            mount_resource_folders={
                "models": "/home/app/.cache/huggingface",
                "experiments": "/home/app/experiments",
            },
            detach_and_interactive=False,
        )

    def get_default_settings(self):
        return LlamaLoraSFTTrainerSettings()

    def create_api(self):
        from .api import LlamaLoraSFTTrainer

        return LlamaLoraSFTTrainer()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import LlamaLoraSFTTrainer, TrainingRun
        from ..llama_lora_server import LlamaLoraServer

        adapter_name = "timer_skill"
        dataset = Path(__file__).parent / "train_example.jsonl"

        training_run = api.execute(
            BrainBoxTask.call(LlamaLoraSFTTrainer).train(adapter_name, dataset)
        )
        yield TestReport.last_call(api).href("Training")
        tc.assertIsInstance(training_run, TrainingRun)
        tc.assertEqual(
            training_run.path,
            api.controller.resource_folder("experiments", adapter_name, training_run.guid),
        )
        tc.assertTrue(training_run.exists())
        for item in ["settings.json", "train.jsonl", "hf_checkpoints", "gguf_checkpoints"]:
            tc.assertTrue((training_run.path / item).exists())

        gguf_checkpoints_dir = training_run.path / "gguf_checkpoints"
        gguf_files = list(gguf_checkpoints_dir.glob("checkpoint-*.gguf"))
        tc.assertTrue(len(gguf_files) > 0, "No GGUF checkpoint files found")
        tc.assertEqual(
            len(gguf_files),
            len(list(gguf_checkpoints_dir.iterdir())),
            "Directory contains non-GGUF files",
        )

        latest_gguf_checkpoint = max(gguf_files, key=lambda f: int(f.stem.split("-")[1]))
        checkpoint_task_name = training_run.guid
        adapter_dest = LlamaLoraServer.controller.resource_folder(
            "lora_adapters", checkpoint_task_name + ".gguf"
        )
        shutil.copy(latest_gguf_checkpoint, adapter_dest)

        timer_prompt = "USER:set a timer for 5 seconds\n"
        tc.assertTrue(api.execute(BrainBoxTask.call(LlamaLoraServer).health()))
        timer_task_result = api.execute(
            BrainBoxTask.call(LlamaLoraServer).completion(
                task_name=checkpoint_task_name, prompt=timer_prompt
            )
        )
        tc.assertEqual(timer_task_result, "HOURS:0\nMINUTES:0\nSECONDS:5\nNAME:_")
        yield (
            TestReport.last_call(api)
            .href("completion")
            .with_comment("Returns only the text result")
        )

        os.remove(adapter_dest)
