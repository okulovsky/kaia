from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration,
    TestReport,
    SmallImageBuilder,
    IImageBuilder,
    DockerWebServiceController,
    IModelDownloadingController,
    BrainBoxApi,
    BrainBoxTask,
    DownloadableModel,
)
from .settings import LlamaLoraServerSettings, HFModel
from pathlib import Path
import subprocess
import time
import platform


class LlamaLoraServerController(
    DockerWebServiceController[LlamaLoraServerSettings], IModelDownloadingController
):
    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return HFModel

    def get_image_builder(self) -> IImageBuilder | None:
        # TODO: other platforms support (e.g. ROCm). See https://github.com/ggml-org/llama.cpp/blob/master/docs/docker.md
        if self._is_arm64_platform():
            source_image = "ghcr.io/kyroninja/llamacpp-arm64:b70bb32"
        elif self._is_cuda_available():
            source_image = "ghcr.io/ggml-org/llama.cpp:server-cuda-b7018"
        else:
            source_image = "ghcr.io/ggml-org/llama.cpp:server-b7018"

        return SmallImageBuilder(
            Path(__file__).parent / "container",
            f'FROM {source_image}\nENTRYPOINT ["/app/llama-server"]',
            None,
        )

    def get_tasknames(self) -> list[str]:
        lora_path = self.resource_folder("lora_adapters")
        file_stems = [name.stem for name in lora_path.iterdir() if name.is_file()]
        self_test_stems = [
            test_adapter.filename.split(".")[0]
            for test_adapter in self.settings.self_test_lora_adapters
        ]
        return sorted(set(file_stems + self_test_stems))

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        cmd_args = [
            "--lora-init-without-apply",
            "--host",
            "0.0.0.0",
            "--model",
            f"/app/models/{self.settings.gguf_model.filename}",
            "--no-mmproj",
        ]

        for taskname in self.get_tasknames():
            path = "/app/lora_adapters/" + taskname + ".gguf"
            cmd_args.extend(["--lora", path])

        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            mount_top_resource_folder=False,
            mount_resource_folders={
                "models": "/app/models",
                "lora_adapters": "/app/lora_adapters",
            },
            command_line_arguments=cmd_args,
        )

    def get_default_settings(self):
        return LlamaLoraServerSettings()

    def pre_install(self):
        self.download_models([self.settings.gguf_model] + self.settings.self_test_lora_adapters)

    def create_api(self):
        from .api import LlamaLoraServer

        return LlamaLoraServer(self.get_tasknames())

    def _is_cuda_available(self) -> bool:
        try:
            subprocess.check_output(["nvidia-smi"])
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _is_arm64_platform(self):
        return platform.machine().lower() in ["arm64", "aarch64"]

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import LlamaLoraServer

        time.sleep(5)  # model loading

        api.execute(BrainBoxTask.call(LlamaLoraServer).health())
        yield (
            TestReport.last_call(api)
            .href("health")
            .with_comment("Returns JSON with `status` field")
        )

        timer_prompt = "USER:set a timer for 5 seconds\n"
        timer_task_result = api.execute(
            BrainBoxTask.call(LlamaLoraServer).completion("timer_self_test", timer_prompt, 30)
        )
        tc.assertIsInstance(timer_task_result, str)
        tc.assertEqual(timer_task_result, "HOURS:0\nMINUTES:0\nSECONDS:5\nNAME:_")
        yield (
            TestReport.last_call(api)
            .href("completion")
            .with_comment("Returns only the text result")
        )

        nutrition_task_result = api.execute(
            BrainBoxTask.call(LlamaLoraServer).completion("nutrition_self_test", timer_prompt, 30)
        )
        tc.assertIsInstance(nutrition_task_result, str)
        tc.assertNotEqual(timer_task_result, nutrition_task_result)
        yield (
            TestReport.last_call(api)
            .href("completion")
            .with_comment("Returns only the text result")
        )
