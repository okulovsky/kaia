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
                 dependencies: Optional[Iterable[str]],
                 add_current_user: bool = True
    ):
        self.code_path = code_path
        self.docker_template = docker_template
        self.dependencies = dependencies
        self.add_current_user = add_current_user

    ADD_USER_PLACEHOLDER = 'add_user'

    PIP_INSTALL_PLACEHOLDER = 'pip_install'

    def _prepare_container_folder(self, executor: IExecutor):
        format_kwargs = {}
        if self.dependencies is not None:
            format_kwargs[SmallImageBuilder.PIP_INSTALL_PLACEHOLDER] = 'RUN pip install --user '+ ' '.join(self.dependencies)
        if self.add_current_user:
            format_kwargs[SmallImageBuilder.ADD_USER_PLACEHOLDER] =user_add_template.format(user_id=executor.get_machine().user_id, group_id=executor.get_machine().group_id)
        dockerfile = self.docker_template.format(**format_kwargs)
        with open(self.code_path / 'Dockerfile', 'w') as file:
            file.write(dockerfile)

    def build_image(self, image_name: str, executor: IExecutor) -> None:
        self._prepare_container_folder(executor)
        args = []
        executor.execute(
            ['docker','build','-t', image_name] + args + ['.'],
            Command.Options(workdir=self.code_path)
        )


