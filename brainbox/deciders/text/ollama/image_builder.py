from brainbox.framework.controllers.brainbox_image_builder.apt_installation import AptInstallation
from brainbox.framework.controllers.brainbox_image_builder.build_context import BuildContext
from ....framework import BrainboxImageBuilder


def _user_commands(context: BuildContext) -> list[str]:
    """Like User().to_commands() but adds -o to allow non-unique UID (ollama base already has UID 1000)."""
    user_id = context.executor.get_machine().user_id
    return [
        f'RUN useradd -ms /bin/bash app -u {user_id} -o && usermod -aG sudo app',
        'USER app',
        'ENV PATH="/home/app/.local/bin:$PATH"',
    ]


class OllamaImageBuilder(BrainboxImageBuilder):
    """BrainboxImageBuilder variant that starts from ollama/ollama:latest.

    The standard builder assumes pip is already available (Python base image).
    Here we first install python3 + pip via apt, then continue normally.
    """

    def __init__(self, root_path, **kwargs):
        super().__init__(root_path, source_image='ollama/ollama:latest', **kwargs)

    def create_dockerfile(self, exec):
        lines = []
        lines.append('FROM ollama/ollama:latest')
        lines.extend(self._create_platform_check_lines())

        # Install miniconda for a clean Python isolated from the OS
        lines.append(
            'RUN apt-get update && apt-get install -y --no-install-recommends wget'
            ' && rm -rf /var/lib/apt/lists/*'
            ' && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh'
            ' && bash /tmp/miniconda.sh -b -p /opt/conda'
            ' && rm /tmp/miniconda.sh'
        )
        lines.append('ENV PATH="/opt/conda/bin:$PATH"')
        lines.append('RUN pip install --no-cache-dir pip==23.2.1 wheel setuptools')

        context = BuildContext(self.root_path, exec)

        if self.apt_install is not None:
            lines.extend(AptInstallation(self.apt_install).to_commands(context))

        if self.custom_apt_installation is not None:
            lines.extend(self.custom_apt_installation)

        if not self.install_requirements_as_root:
            lines.extend(_user_commands(context))

        if self.dependencies is not None:
            for dep in self.dependencies:
                lines.extend(dep.to_commands(context))

        if self.finishing_installation_steps is not None:
            lines.extend(self.finishing_installation_steps)

        if self.install_requirements_as_root:
            lines.extend(_user_commands(context))

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