import uuid

from foundation_kaia.misc import Loc
import shutil
import os
import toml
from .small_image_builder import SmallImageBuilder, IImageBuilder
from ..executor import IExecutor
from pathlib import Path
from typing import Iterable

class RepoImageBuilder(IImageBuilder):
    def __init__(self,
                 dockerfile_template: str,
                 repo_folders: tuple[str,...],
                 container_folder_name: str|None = None,
                 dockerignore: tuple[str,...]|None = None,
                 additional_dependencies: tuple[str,...] = ()
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
        self.additional_dependencies = additional_dependencies

    def build_image(self, image_name: str, exec: IExecutor) -> None:
        return self._create_builder().build_image(image_name, exec)

    @staticmethod
    def collect_dependencies_from_folders(folders: Iterable[Path], additional_toml_paths: list[list[str]]|None = None) -> list[str]:
        dependencies = []
        for folder in folders:
            filename = folder/'pyproject.toml'
            if not filename.is_file():
                continue
            toml_data = toml.loads(filename.read_text())
            paths = [
                ['project', 'dependencies']
            ]
            if additional_toml_paths is not None:
                paths.extend(additional_toml_paths)

            for toml_path in paths:

                section = toml_data
                for item in toml_path:
                    if item in section:
                        section = section[item]
                    else:
                        section = None
                        break

                if section is None:
                    continue

                section_dependencies = []
                for d in section:
                    if d.startswith('kaia-'):
                        continue
                    if d in dependencies:
                        continue
                    section_dependencies.append(d)

                #print(folder, toml_path, section_dependencies)
                dependencies.extend(section_dependencies)

        return dependencies


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

        dependencies = RepoImageBuilder.collect_dependencies_from_folders(
            src_folder/folder for folder in self.repo_folders
        )

        for dep in self.additional_dependencies:
            if dep not in dependencies:
                dependencies.append(dep)

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
