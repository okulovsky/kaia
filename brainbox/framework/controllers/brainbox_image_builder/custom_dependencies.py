from .build_context import BuildContext
from yo_fluq import FileIO
from .builder_part import IBuilderPart
from dataclasses import dataclass

@dataclass
class CustomDependencies(IBuilderPart):
    packages: tuple[str, ...]
    no_build_isolation: bool = False
    no_binary: tuple[str,...]|None = None
    index_url: str | None = None


    def to_commands(self, context: BuildContext) -> list[str]:
        packages = ' '.join(self.packages)
        wheel_arguments = []
        if self.no_build_isolation:
            wheel_arguments.append('--no-build-isolation')
        if self.no_binary is not None:
            wheel_arguments.append('--no-binary')
            wheel_arguments.append(','.join(self.no_binary))
        if self.index_url is not None:
            wheel_arguments.append('--index-url')
            wheel_arguments.append(self.index_url)
        wheel_arguments_str = ' '.join(wheel_arguments)

        return [(
            f'RUN pip wheel --no-cache-dir --wheel-dir=/tmp/wheels {wheel_arguments_str} {packages} && '
            f'pip install --no-cache-dir --no-index --find-links=/tmp/wheels {packages} && '
            f'rm -rf /tmp/wheels'
        )]

