import os
from dataclasses import dataclass, field
from pathlib import Path
from .repository import Repository
from yo_fluq import FileIO
from ...deployment import IImageBuilder, IExecutor, Command
from .apt_installation import AptInstallation
from .build_context import BuildContext
from .user import User
from .dependencies import Dependencies
from .custom_dependencies import CustomDependencies
from .pytorch_dependencies import PytorchDependencies

@dataclass
class BrainboxImageBuilder(IImageBuilder):
    root_path: Path
    source_image: str
    apt_install: tuple[str,...]|None = None
    repository: Repository|None = None

    install_requirements_as_root: bool = False
    allow_arm64: bool = False
    build_command: tuple[str,...] | None = None
    custom_apt_installation: tuple[str,...] | None = None
    custom_dependencies: tuple[Dependencies|CustomDependencies|PytorchDependencies,...]|None = None
    keep_dockerfile: bool = False

    Repository = Repository
    Dependencies = Dependencies
    CustomDependencies = CustomDependencies
    PytorchDependencies = PytorchDependencies

    @property
    def source_is_python(self):
        return ':' not in self.source_image

    @property
    def context(self) -> BuildContext:
        return BuildContext(self.root_path, None)

    def create_dockerfile(self, exec):
        lines = []
        source = self.source_image
        if self.source_is_python:
            source = f'python:{source}'
        lines.append(f'FROM {source}')

        lines.extend(self._create_platform_check_lines())

        context = BuildContext(self.root_path, exec)

        if self.apt_install is not None:
            lines.extend(AptInstallation(self.apt_install).to_commands(context))

        if self.custom_apt_installation is not None:
            lines.extend(self.custom_apt_installation)

        if not self.install_requirements_as_root:
            lines.extend(User().to_commands(context))

        if self.custom_dependencies is None:
            lines.extend(Dependencies().to_commands(context))
        else:
            for dep in self.custom_dependencies:
                lines.extend(dep.to_commands(context))

        if self.install_requirements_as_root:
            lines.extend(User().to_commands(context))

        lines.append('WORKDIR /home/app')

        if self.repository is not None:
            lines.extend(self.repository.to_commands(context))

        if (self.root_path / 'local_fix').exists():
            lines.append('COPY local_fix/ /home/app/.local')
        lines.append('COPY app/ /home/app/main')
        lines.append('ENTRYPOINT ["python3","/home/app/main/main.py"]')
        return '\n\n'.join(lines)



    def build_image(self, image_name: str, exec: IExecutor) -> None:
        FileIO.write_text(
            self.create_dockerfile(exec),
            self.root_path/'Dockerfile'
        )
        args = []
        command = ['docker', 'build']
        if self.build_command is not None:
            command = ['docker'] + list(self.build_command)
        exec.execute(
            command + ['-t', image_name] + args + ['.'],
            Command.Options(workdir=self.root_path)
        )
        if not self.keep_dockerfile:
            os.unlink(self.root_path/'Dockerfile')



    def _create_platform_check_lines(self):
        allowed_platforms = ["x86_64", "amd64"]
        if self.allow_arm64:
            allowed_platforms.extend(["aarch64","arm64" ])

        ifs = []
        for platform in allowed_platforms:
            ifs.append(f'[ "$arch" = "{platform}" ]')
            ifs.append(' || ')

        msg = 'Build requires ' + ', '.join(allowed_platforms)+', but platform was $arch'

        return [
            'RUN arch="$(uname -m)"; '+''.join(ifs)+ '{ echo >&2 "' + msg + '"; exit 1; }'
        ]



