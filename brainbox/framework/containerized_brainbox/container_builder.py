import os
import shutil

from foundation_kaia.misc import Loc
from brainbox.framework.deployment import SmallImageBuilder, LocalExecutor
from pathlib import Path


def create_brainbox_builder():
    bb_folder = Path(__file__).parent.parent.parent
    build_folder = Loc.temp_folder/'brain_box_container'
    if build_folder.is_dir():
        shutil.rmtree(build_folder)
    os.makedirs(build_folder)
    return SmallImageBuilder(
        build_folder,
        TEMPLATE,
        [d for d in DEPENDENCIES.split('\n') if d.strip()!=''],
        add_current_user=True,
        copy_to_code_path={
            bb_folder.parent/'foundation_kaia': '/foundation_kaia',
            bb_folder/'framework' : '/brainbox/framework',
            bb_folder/'deciders': '/brainbox/deciders',
            bb_folder/'run.py': '/brainbox/run.py',
            bb_folder/'__init__.py': '/brainbox/__init__.py',
            },
        write_to_code_path={
            '/pyproject.toml': TOML
        }
    )

DOCKER_INSTALL = '''
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       gnupg \
       lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*
'''


TEMPLATE = f'''
FROM python:3.11.11

{DOCKER_INSTALL}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

COPY --chown=app:app . /home/app

RUN pip install --user -e .

ENTRYPOINT ["python", "-m", "brainbox.run"]
'''

TOML = '''
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
version = "0.0.0"
name = "brainbox-container"

[tool.setuptools]
packages = ["brainbox", "foundation_kaia"]


'''

DEPENDENCIES = """
requests
jsonpickle
Jinja2
fastapi
uvicorn
python-multipart
websocket-client
python-dotenv
websockets
pyyaml
docutils

yo_fluq
sqlalchemy
soundfile
toml
pandas
huggingface_hub
"""

if __name__ == '__main__':
    create_brainbox_builder().build_image('brainbox', LocalExecutor())