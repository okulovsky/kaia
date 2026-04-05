import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from .repository import Repository
from yo_fluq import FileIO
from ...deployment import IImageBuilder, IExecutor, Command
from .apt_installation import AptInstallation
from .build_context import BuildContext
from .user import User
from .dependencies import *


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
    dependencies: tuple[IDependency,...]|None = None
    keep_dockerfile: bool = False
    copy_foundation_kaia: bool = True

    Repository = Repository
    RequirementsLockTxt = RequirementsDependencies
    CustomDependencies = CustomDependencies
    PytorchDependencies = PytorchDependencies
    KaiaFoundationDependencies = KaiaFoundationDependencies

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

        lines.append("RUN pip install --no-cache-dir pip==23.2.1 wheel setuptools")

        context = BuildContext(self.root_path, exec)

        if self.apt_install is not None:
            lines.extend(AptInstallation(self.apt_install).to_commands(context))

        if self.custom_apt_installation is not None:
            lines.extend(self.custom_apt_installation)

        if not self.install_requirements_as_root:
            lines.extend(User().to_commands(context))

        if self.dependencies is None:
            pass
        else:
            for dep in self.dependencies:
                lines.extend(dep.to_commands(context))

        if self.install_requirements_as_root:
            lines.extend(User().to_commands(context))

        lines.append('WORKDIR /home/app')

        if self.repository is not None:
            lines.extend(self.repository.to_commands(context))

        if (self.root_path / 'local_fix').exists():
            lines.append('COPY local_fix/ /home/app/.local')

        if self.copy_foundation_kaia:
            lines.extend(self._copy_foundation_kaia())

        lines.append('COPY app/ /home/app/main')
        lines.append('ENTRYPOINT ["python3","/home/app/main/main.py"]')
        return '\n\n'.join(lines)



    def build_image(self, image_name: str, exec: IExecutor) -> None:
        try:
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
        finally:
            dockerfile = self.root_path/'Dockerfile'
            if dockerfile.exists() and not self.keep_dockerfile:
                os.unlink(dockerfile)

            kaia_path = self.root_path/'foundation_kaia'
            if kaia_path.exists():
                shutil.rmtree(kaia_path)



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



    def _copy_foundation_kaia(self):
        path = self.root_path
        while True:
            new_path = path.parent
            if new_path == path:
                break
            path = new_path
            if (path/'foundation_kaia').exists():
                break


        source_path = path/'foundation_kaia'
        target_path = self.root_path/'foundation_kaia'
        if target_path.is_dir():
            shutil.rmtree(target_path)
        shutil.copytree(source_path, target_path)
        return [
            'COPY --chown=app:app foundation_kaia/marshalling_2 /home/app/foundation_kaia_src/foundation_kaia/marshalling_2',
            'COPY --chown=app:app foundation_kaia/brainbox_utils /home/app/foundation_kaia_src/foundation_kaia/brainbox_utils',
            'COPY --chown=app:app foundation_kaia/logging /home/app/foundation_kaia_src/foundation_kaia/logging',
            'COPY --chown=app:app foundation_kaia/fork /home/app/foundation_kaia_src/foundation_kaia/fork',
            'COPY --chown=app:app foundation_kaia/misc /home/app/foundation_kaia_src/foundation_kaia/misc',
            'COPY --chown=app:app foundation_kaia/__init__.py /home/app/foundation_kaia_src/foundation_kaia/__init__.py',
            'ENV PYTHONPATH="/home/app/foundation_kaia_src:$PYTHONPATH"',
        ]
