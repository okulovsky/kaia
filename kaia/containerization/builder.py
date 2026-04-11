from dataclasses import dataclass
from brainbox.framework.deployment import SmallImageBuilder
from pathlib import Path
from foundation_kaia.misc import Loc
import shutil
import os
import toml

DEFAULT_FOLDERS = (
    'foundation_kaia',
    'brainbox',
    'grammatron',
    'eaglesong',
    'avatar',
    'chara',
    'kaia',
    'talents',
)

@dataclass
class KaiaImageBuilder:
    additional_folders: tuple[str,...] = ()
    entry_point: str = 'kaia.containerization.main'
    container_folder_name: str = 'kaia_container'

    def create_builder(self):
        build_folder = Loc.temp_folder / self.container_folder_name
        if build_folder.is_dir():
            shutil.rmtree(build_folder)
        os.makedirs(build_folder)

        src_folder = Loc.root_folder
        all_folders = DEFAULT_FOLDERS+self.additional_folders
        copy_to_code_path = {}
        for folder in all_folders:
            copy_to_code_path[src_folder/folder] = '/'+folder

        toml_data = toml.loads(TOML)
        toml_data["tool"]["setuptools"]["packages"] = list(all_folders)
        final_toml = toml.dumps(toml_data)

        dependencies = []
        for folder in all_folders:
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
            TEMPLATE.replace('#ENTRYPOINT', self.entry_point),
            dependencies,
            add_current_user=True,
            copy_to_code_path=copy_to_code_path,
            write_to_code_path={
                '/pyproject.toml': final_toml,
            }
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

TEMPLATE = f'''
FROM python:3.11

RUN apt-get update \
    && apt-get install -y curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY --chown=app:app . /home/app

WORKDIR /home/app

RUN pip install  --no-cache-dir --no-compile --user -e .

ENTRYPOINT ["python", "-m", "#ENTRYPOINT"]
'''