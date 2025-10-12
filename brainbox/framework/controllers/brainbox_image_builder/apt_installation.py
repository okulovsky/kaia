from dataclasses import dataclass
from .builder_part import IBuilderPart, BuildContext

@dataclass
class AptInstallation(IBuilderPart):
    packages: tuple[str,...]

    def to_commands(self, context: BuildContext) -> list[str]:
        libs = ' '.join(self.packages)
        return [(
            'RUN apt-get update && '
            f'apt-get install -y --no-install-recommends {libs} && '
            'rm -rf /var/lib/apt/lists/*'
        )]