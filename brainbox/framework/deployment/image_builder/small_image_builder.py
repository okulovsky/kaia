import os
import shutil
import uuid
from typing import *
from pathlib import Path
from .image_builder import IImageBuilder
from ..executor import IExecutor, Command


user_add_template = '''
RUN useradd -ms /bin/bash app -u {user_id}

RUN usermod -aG sudo app

USER app
'''

class SmallImageBuilder(IImageBuilder):
    def __init__(self,
                 code_path: Path,
                 docker_template: str,
                 dependencies: Optional[Iterable[str]|Iterable[Iterable[str]]],
                 add_current_user: bool = True,
                 copy_to_code_path: dict[Path, str]|None = None
    ):
        self.code_path = code_path
        self.docker_template = docker_template
        self.dependencies = self._make_dependencies(dependencies)
        self.add_current_user = add_current_user
        self.copy_to_code_path = copy_to_code_path

    ADD_USER_PLACEHOLDER = 'add_user'

    PIP_INSTALL_PLACEHOLDER = 'pip_install'

    def _make_dependencies(self, dependencies) -> list[list[str]]|None:
        if dependencies is None:
            return None
        deps = list(dependencies)
        if all(isinstance(element,str) for element in deps):
            deps = [deps]
        else:
            deps = [list(element) for element in dependencies]
        return deps

    def _convert_dependencies(self):
        if self.dependencies is None:
            return None
        result = []
        for line in self.dependencies:
            template = (
                'RUN pip wheel --no-cache-dir --wheel-dir=/tmp/wheels {DEPS} && '  
                'pip install --no-cache-dir --no-index --find-links=/tmp/wheels {DEPS} && '
                'rm -rf /tmp/wheels'
            )
            result.append(template.format(DEPS=' '.join(line)))
        return '\n\n'.join(result)


    def _prepare_container_folder(self, executor: IExecutor):
        format_kwargs = {}
        if self.dependencies is not None:
            format_kwargs[SmallImageBuilder.PIP_INSTALL_PLACEHOLDER] = self._convert_dependencies()
        if self.add_current_user:
            format_kwargs[SmallImageBuilder.ADD_USER_PLACEHOLDER] = user_add_template.format(user_id=executor.get_machine().user_id, group_id=executor.get_machine().group_id)

        dockerfile = self.docker_template.format(**format_kwargs)
        os.makedirs(self.code_path, exist_ok=True)
        with open(self.code_path / 'Dockerfile', 'w') as file:
            file.write(dockerfile)

        if self.copy_to_code_path is not None:
            for source_path, target_str_path in self.copy_to_code_path.items():
                target = target_str_path
                while target.startswith('/'):
                    target = target[1:]
                target = self.code_path / target
                target.relative_to(self.code_path)
                if target.is_file():
                    os.unlink(target)
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                if source_path.is_file():
                    os.makedirs(target.parent, exist_ok=True)
                    shutil.copy(source_path, target)
                elif source_path.is_dir():
                    shutil.copytree(source_path, target)
                else:
                    raise ValueError(f"{source_path} is neither file nor directory")


    def build_image(self, image_name: str, executor: IExecutor) -> None:
        self._prepare_container_folder(executor)
        args = []
        executor.execute(
            ['docker','build','-t', image_name] + args + ['.'],
            Command.Options(workdir=self.code_path)
        )

    @staticmethod
    def APT_INSTALL(libs: str):
        return (
            'RUN apt-get update && '
            f'apt-get install -y --no-install-recommends {libs} && '
            'rm -rf /var/lib/apt/lists/*'
        )


    @staticmethod
    def GIT_CLONE_AND_RESET(repo, folder, commit=None, options='', install=True):
        result = []
        result.append(f'RUN git clone {repo} {folder}')
        result.append(f' && cd {folder}')
        if commit is not None:
            result.append(f' && git reset --hard {commit}')
        result.append(' && rm -rf .git')
        if install:
            result.append(f' && pip install --user -e .{options}')
            result.append(' && rm -rf ~/.cache/pip')
        return ''.join(result)
