import uuid
from typing import *
from pathlib import Path
from .container_builder import IContainerBuilder
from ..executors import LocalExecutor, ExecuteOptions, IExecutor



class SmallContainerBuilder(IContainerBuilder):
    def __init__(self,
                 image_name: str,
                 code_path: Path,
                 docker_template: str,
                 dependencies: str,
    ):
        self.image_name = image_name
        self.code_path = code_path
        self.docker_template = docker_template
        self.dependencies = dependencies
        self.executor = LocalExecutor()

    def get_local_name(self) -> str:
        return self.image_name

    def _prepare_container_folder(self):
        deps = ' '.join(self.dependencies.split('\n'))
        docker = self.docker_template.format(dependencies=deps)
        with open(self.code_path / 'Dockerfile', 'w') as file:
            file.write(docker)

    def build_container(self) -> None:
        self._prepare_container_folder()
        self.executor.execute(['docker','build','-t', self.image_name,'.'], ExecuteOptions(workdir=self.code_path))



class RemoteSmallContainerBuilder(IContainerBuilder):
    def __init__(self,
                 inner_builder: SmallContainerBuilder,
                 tmp_folder: Path,
                 executor: IExecutor
    ):
        self.inner_builder = inner_builder
        self.tmp_folder = tmp_folder
        self.executor = executor

    def build_container(self) -> None:
        from yo_fluq_ds import Query

        self.inner_builder._prepare_container_folder()
        remote_folder = self.tmp_folder/str(uuid.uuid4())
        for file_ in Query.folder(self.inner_builder.code_path, '**/*'):
            file: Path = file_
            if not file.is_file():
                continue
            rel_path = file.relative_to(self.inner_builder.code_path)
            remote_path = remote_folder/rel_path
            print(f"copying file {file} -> {remote_path}")
            self.executor.create_empty_folder(remote_path.parent)
            self.executor.upload_file(file, str(remote_path))
        self.executor.execute(['docker','build','-t',self.inner_builder.image_name,remote_folder])

    def get_local_name(self) -> str:
        return self.inner_builder.get_local_name()


