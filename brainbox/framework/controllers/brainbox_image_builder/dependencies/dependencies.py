from .common import BuildContext, IDependency
from yo_fluq import FileIO

from dataclasses import dataclass

@dataclass
class RequirementsDependencies(IDependency):
    no_deps: bool = True

    def to_commands(self, context: BuildContext) -> list[str]:
        result = []
        if context.requirements_preinstall.is_file():
            build_requirements = FileIO.read_text(context.requirements_preinstall).replace('\n', ' ')
            result.append('RUN '+self._create_one_dependency_command(build_requirements))
        result.append(f'ARG REQ={context.requirements_lock.name}')
        result.append(f'COPY {context.requirements_lock.name} /tmp/requirements.txt')
        result.append('RUN '+self._create_one_dependency_command('-r /tmp/requirements.txt'))
        return result


    def _create_one_dependency_command(self, packages):
        if self.no_deps:
            no_deps = '--no-deps'
        else:
            no_deps = ''
        return (
            f'pip wheel {no_deps} --prefer-binary --no-build-isolation --no-cache-dir --wheel-dir=/tmp/wheels {packages} && '
            f'pip install {no_deps} --no-cache-dir --no-index --find-links=/tmp/wheels {packages} && '
            f'rm -rf /tmp/wheels'
        )