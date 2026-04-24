import uuid

from foundation_kaia.misc import Loc
import shutil
import os
import toml
from .small_image_builder import SmallImageBuilder, IImageBuilder
from ..executor import IExecutor

class RepoImageBuilder(IImageBuilder):
    def __init__(self,
                 dockerfile_template: str,
                 repo_folders: tuple[str,...],
                 container_folder_name: str|None = None,
                 dockerignore: tuple[str,...]|None = None
                 ):
        self.dockerfile_template = dockerfile_template
        self.repo_folders = repo_folders
        if container_folder_name is None:
            container_folder_name = str(uuid.uuid4())
        self.container_folder_name = container_folder_name
        if dockerignore is None:
            dockerignore = (
                '**/__pycache__/',
                '**/*.pyc',
                '**/*.pyo',
            )
        self.dockerignore = dockerignore

    def build_image(self, image_name: str, exec: IExecutor) -> None:
        return self._create_builder().build_image(image_name, exec)

    def _create_builder(self):
        build_folder = Loc.temp_folder / 'containers' / self.container_folder_name
        if build_folder.is_dir():
            shutil.rmtree(build_folder)
        os.makedirs(build_folder)

        src_folder = Loc.root_folder
        copy_to_code_path = {}
        for folder in self.repo_folders:
            copy_to_code_path[src_folder/folder] = '/'+folder

        toml_data = toml.loads(TOML)
        toml_data["tool"]["setuptools"]["packages"] = list(self.repo_folders)
        final_toml = toml.dumps(toml_data)

        dependencies = []
        for folder in self.repo_folders:
            filename = src_folder/folder/'pyproject.toml'
            if not filename.is_file():
                continue
            toml_data = toml.loads(filename.read_text())
            for d in toml_data['project']['dependencies']:
                if d.startswith('kaia-'):
                    continue
                if d in dependencies:
                    continue
                dependencies.append(d)

        return SmallImageBuilder(
            build_folder,
            self.dockerfile_template,
            dependencies,
            add_current_user=True,
            copy_to_code_path=copy_to_code_path,
            write_to_code_path={
                '/pyproject.toml': final_toml,
            },
            docker_ignore=self.dockerignore
        )


TOML = '''
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
version = "0.0.0"
name = "kaia-container"

[tool.setuptools]
packages = []

'''
