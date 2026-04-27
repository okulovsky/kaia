from dataclasses import dataclass
from .common import IDependency, BuildContext


@dataclass
class KaiaFoundationDependencies(IDependency):
    PACKAGES = [
        'requests<=2.32.5',
        'fastapi<=0.131.0',
        'uvicorn<=0.41.0',
        'websocket-client<=1.9.0',
        'python-dotenv<=1.2.1',
        'websockets<=16.0',
        'tqdm<=4.67.3',
        'notebook<=7.5.3',
        'pyyaml<=6.0.3',
    ]

    def to_commands(self, context: BuildContext) -> list[str]:
        packages_str = ' '.join(f"'{p}'" for p in self.PACKAGES)
        return [(
            f'RUN pip wheel --no-build-isolation --no-cache-dir --wheel-dir=/tmp/wheels {packages_str} && '
            f'pip install --no-cache-dir --no-index --find-links=/tmp/wheels {packages_str} && '
            f'rm -rf /tmp/wheels'
        )]
