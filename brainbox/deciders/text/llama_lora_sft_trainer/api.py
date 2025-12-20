from brainbox.framework import OnDemandDockerApi, FileLike, FileIO, RunConfiguration
from .controller import LlamaLoraSFTTrainerController
from .container.app.settings import TrainingSettings
from .settings import LlamaLoraSFTTrainerSettings
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingRun:
    """
    Represents a single training run.
    """

    adapter_name: str
    guid: str
    path: Path

    def exists(self) -> bool:
        return self.path.exists()


class LlamaLoraSFTTrainer(
    OnDemandDockerApi[LlamaLoraSFTTrainerSettings, LlamaLoraSFTTrainerController]
):
    def train(
        self,
        adapter_name: str,
        dataset: FileLike.Type,
        settings: TrainingSettings | dict | None = None,
    ) -> TrainingRun:
        """
        Runs training and returns a TrainingRun pointing to the folder:

            .../resources/LlamaLoraSFTTrainer/experiments/{adapter_name}/{guid}/
        """
        guid = uuid.uuid4().hex
        run = TrainingRun(
            adapter_name=adapter_name,
            guid=guid,
            path=self.controller.resource_folder("experiments", adapter_name, guid),
        )

        if settings is None:
            settings = TrainingSettings()
        elif isinstance(settings, dict):
            settings = TrainingSettings(**settings)
        FileIO.write_json(
            settings.__dict__,
            run.path / "settings.json",
        )

        with FileLike(dataset, self.cache_folder) as content:
            FileIO.write_bytes(content.read(), run.path / "train.jsonl")

        cmd_args = ["--adapter-name", adapter_name, "--guid", guid]

        configuration = RunConfiguration(
            detach_and_interactive=False,
            set_env_variables={"PYTHONUNBUFFERED": "1"},
            custom_flags=["--tty"], # for tqdm bars
            mount_resource_folders={
                "models": "/home/app/.cache/huggingface",
                "experiments": "/home/app/experiments",
            },
            command_line_arguments=cmd_args,
        )

        self.controller.run_with_configuration(configuration)

        return run

    Controller = LlamaLoraSFTTrainerController
    Settings = LlamaLoraSFTTrainerSettings
    TrainingSettings = TrainingSettings
