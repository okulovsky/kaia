import re
from ....framework import BrainboxImageBuilder


class LlamaCppImageBuilder(BrainboxImageBuilder):
    """BrainboxImageBuilder variant that starts from a llama.cpp server image.

    The standard builder assumes pip is already available (Python base image).
    Here we first install miniconda, then continue normally.
    """

    def create_dockerfile(self, exec):
        lines = super().create_dockerfile(exec).split('\n\n')
        # After FROM and the platform check, before the first pip call
        lines[2:2] = [
            'RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates'
            ' && rm -rf /var/lib/apt/lists/*'
            ' && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh -O /tmp/miniconda.sh'
            ' && bash /tmp/miniconda.sh -b -p /opt/conda'
            ' && rm /tmp/miniconda.sh',
            'ENV PATH="/opt/conda/bin:$PATH"',
        ]
        dockerfile = '\n\n'.join(lines)
        # The base image may already have a user with this UID
        return re.sub(r'(useradd -ms /bin/bash app -u \d+)', r'\1 -o', dockerfile)
