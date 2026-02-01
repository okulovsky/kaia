from .build_context import BuildContext
from yo_fluq import FileIO
from .builder_part import IBuilderPart
from dataclasses import dataclass

@dataclass
class PytorchDependencies(IBuilderPart):
    pytorch_version: str
    cuda_version: str|None = 'cu124'
    torchaudio_version: str|None|bool = None
    torchvideo_version: str|None = None


    def __post_init__(self):
        if isinstance(self.torchaudio_version, bool):
            if self.torchaudio_version:
                self.torchaudio_version = self.pytorch_version
            else:
                self.torchaudio_version = None

    def to_commands(self, context: BuildContext) -> list[str]:
        packages: list[str] = [f"torch=={self.pytorch_version}"]

        if self.torchaudio_version is not None:
            packages.append(f"torchaudio=={self.torchaudio_version}")

        if self.torchvideo_version is not None:
            packages.append(f"torchvision=={self.torchvideo_version}")

        pkgs = " ".join(packages)

        index_url = (
            f"https://download.pytorch.org/whl/{self.cuda_version}"
            if self.cuda_version is not None
            else "https://download.pytorch.org/whl/cpu"
        )

        lines: list[str] = [
            "RUN set -eu; \\",
            '    arch="$(uname -m)"; \\',
            '    if [ "$arch" = "x86_64" ] || [ "$arch" = "amd64" ]; then \\',
        ]

        # amd64 / x86_64
        lines += [
            f"        pip wheel --no-cache-dir --wheel-dir=/tmp/wheels "
            f"--index-url {index_url} {pkgs}; \\",
        ]

        lines += [
            f"        pip install --no-cache-dir --no-index --find-links=/tmp/wheels {pkgs}; \\",
            "        rm -rf /tmp/wheels; \\",
            '    elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \\',
            f"        pip wheel --no-cache-dir --wheel-dir=/tmp/wheels {pkgs}; \\",
            f"        pip install --no-cache-dir --no-index --find-links=/tmp/wheels {pkgs}; \\",
            "        rm -rf /tmp/wheels; \\",
            "    else \\",
            '        echo >&2 "Unsupported platform: $arch"; \\',
            "        exit 1; \\",
            "    fi",
        ]

        return ['\n'.join(lines)]