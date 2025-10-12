import os
import shutil
import uuid
from typing import *
from pathlib import Path
from .image_builder import IImageBuilder
from ..executor import IExecutor, Command
from yo_fluq import FileIO


user_add_template = '''
RUN useradd -ms /bin/bash app -u {user_id}

RUN usermod -aG sudo app

USER app
'''

class SmallImageBuilder(IImageBuilder):
    def __init__(self,
                 code_path: Path,
                 docker_template: str|None,
                 dependencies: Optional[Iterable[str]|Iterable[Iterable[str]]],
                 add_current_user: bool = True,
                 copy_to_code_path: dict[Path, str]|None = None,
                 write_to_code_path: dict[str, str]|None = None,
                 reset_code_folder: bool = False,
                 build_command: Optional[Iterable[str]] = None,
                 docker_ignore:tuple[str,...]|None = ('**/__pycache__/', '**/*.pyc', '**/*.pyo')
    ):
        self.code_path = code_path
        self.docker_template = docker_template
        self.dependencies = self._make_dependencies(dependencies)
        self.add_current_user = add_current_user
        self.copy_to_code_path = copy_to_code_path
        self.reset_code_folder = reset_code_folder
        self.write_to_code_path = write_to_code_path
        self.build_command = build_command
        self.docker_ignore = docker_ignore

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

    @staticmethod
    def create_dependency_command(dependencies):
        template = (
            'pip wheel --no-cache-dir --wheel-dir=/tmp/wheels {DEPS} && '  
            'pip install --no-cache-dir --no-index --find-links=/tmp/wheels {DEPS} && '
            'rm -rf /tmp/wheels'
        )
        return template.format(DEPS=' '.join(dependencies))


    def _convert_dependencies(self):
        if self.dependencies is None:
            return None
        result = []
        for line in self.dependencies:
            result.append('RUN '+SmallImageBuilder.create_dependency_command(line))
        return '\n\n'.join(result)

    def _create_target_file(self, target_str_path: str):
        target = target_str_path
        while target.startswith('/'):
            target = target[1:]
        target = self.code_path / target
        target.relative_to(self.code_path)
        if target.is_file():
            os.unlink(target)
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        return target

    def _prepare_container_folder(self, executor: IExecutor):
        if self.docker_template is not None:
            format_kwargs = {}
            if self.dependencies is not None:
                format_kwargs[SmallImageBuilder.PIP_INSTALL_PLACEHOLDER] = self._convert_dependencies()
            if self.add_current_user:
                format_kwargs[SmallImageBuilder.ADD_USER_PLACEHOLDER] = user_add_template.format(user_id=executor.get_machine().user_id, group_id=executor.get_machine().group_id)

            dockerfile = self.docker_template.format(**format_kwargs)
            if self.reset_code_folder:
                shutil.rmtree(self.code_path, ignore_errors=True)
            os.makedirs(self.code_path, exist_ok=True)
            with open(self.code_path / 'Dockerfile', 'w', encoding='utf-8') as file:
                file.write(dockerfile)

        if self.copy_to_code_path is not None:
            for source_path, target_str_path in self.copy_to_code_path.items():
                target = self._create_target_file(target_str_path)
                if source_path.is_file():
                    os.makedirs(target.parent, exist_ok=True)
                    shutil.copy(source_path, target)
                elif source_path.is_dir():
                    shutil.copytree(source_path, target)
                else:
                    raise ValueError(f"{source_path} is neither file nor directory")

        if self.write_to_code_path is not None:
            for target_str_path, content in self.write_to_code_path.items():
                target = self._create_target_file(target_str_path)
                FileIO.write_text(content, target)

        if self.docker_ignore is not None:
            with open(self.code_path/'.dockerignore', 'w', encoding='utf-8') as file:
                for line in self.docker_ignore:
                    file.write(line+"\n")



    def build_image(self, image_name: str, executor: IExecutor) -> None:
        self._prepare_container_folder(executor)
        args = []
        command = ['docker', 'build']
        if self.build_command is not None:
            command = ['docker'] + list(self.build_command)
        executor.execute(
            command + ['-t', image_name] + args + ['.'],
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
