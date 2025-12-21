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
from .settings import LlamaLoraServerSettings
from .model import HFResource
from pathlib import Path
import subprocess
import platform


class LlamaLoraServerController(
    DockerWebServiceController[LlamaLoraServerSettings], IModelDownloadingController
):
    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return HFResource

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

    def get_tasknames(self, model_id: str) -> list[str]:
        lora_path = self.resource_folder("models", model_id, "lora_adapters")
        file_stems = [name.stem for name in lora_path.iterdir() if name.is_file()]
        return sorted(file_stems)

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is None:
            raise ValueError(f"`parameter` cannot be None for {self.get_name()}")
        cmd_args = [
            "--lora-init-without-apply",
            "--host",
            "0.0.0.0",
            "--model",
            f"/app/models/{parameter}/model.gguf",
            "--no-mmproj",
        ]

        for taskname in self.get_tasknames(parameter):
            path = f"/app/models/{parameter}/lora_adapters/{taskname}.gguf"
            cmd_args.extend(["--lora", path])

        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            mount_top_resource_folder=False,
            mount_resource_folders={
                "models": "/app/models",
            },
            command_line_arguments=cmd_args,
        )

    def get_default_settings(self):
        return LlamaLoraServerSettings()

    def pre_install(self):
        self.download_models(
            self.settings.self_test_lora_adapters + self.settings.gguf_models_to_download
        )

    def create_api(self):
        from .api import LlamaLoraServer

        return LlamaLoraServer()

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

        model_id = self.settings.gguf_models_to_download[0].model_id

        health_result = api.execute(BrainBoxTask.call(LlamaLoraServer, model_id).health())
        tc.assertTrue(health_result)
        yield (TestReport.last_call(api).href("health").with_comment("Returns boolean status"))

        timer_prompt1 = "USER:set a timer for 5 seconds\n"
        timer_prompt2 = "USER:set a timer for 10 seconds\n"

        timer_task_result = api.execute(
            BrainBoxTask.call(LlamaLoraServer, model_id).completion(
                task_name="timer_self_test", prompt=timer_prompt1
            )
        )
        tc.assertIsInstance(timer_task_result, str)
        tc.assertEqual(timer_task_result, "HOURS:0\nMINUTES:0\nSECONDS:5\nNAME:_")
        yield (
            TestReport.last_call(api)
            .href("completion")
            .with_comment("Returns only the text result")
        )

        nutrition_task_result = api.execute(
            BrainBoxTask.call(LlamaLoraServer, model_id).completion(
                task_name="nutrition_self_test", prompt=timer_prompt1
            )
        )
        tc.assertIsInstance(nutrition_task_result, str)
        tc.assertNotEqual(timer_task_result, nutrition_task_result)
        yield (
            TestReport.last_call(api)
            .href("completion")
            .with_comment("Returns only the text result")
        )

        multiple_prompts_result = api.execute(
            BrainBoxTask.call(LlamaLoraServer, model_id).completion(
                task_name="timer_self_test", prompts=[timer_prompt1, timer_prompt2]
            )
        )
        tc.assertIsInstance(multiple_prompts_result, list)
        tc.assertEqual(len(multiple_prompts_result), 2)
        tc.assertEqual(multiple_prompts_result[0], "HOURS:0\nMINUTES:0\nSECONDS:5\nNAME:_")
        tc.assertEqual(multiple_prompts_result[1], "HOURS:0\nMINUTES:0\nSECONDS:10\nNAME:_")
        yield (
            TestReport.last_call(api)
            .href("completion")
            .with_comment("Returns only the text result for multiple prompts")
        )
