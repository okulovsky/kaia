import os
import shutil

from brainbox.framework import Loc
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
            bb_folder/'framework' : '/brainbox/framework',
            bb_folder/'deciders': '/brainbox/deciders',
            bb_folder/'run.py': '/brainbox/run.py',
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
'''

DEPENDENCIES = """
asttokens==3.0.0
blinker==1.9.0
certifi==2024.12.14
charset-normalizer==3.4.1
click==8.1.8
comm==0.2.2
contourpy==1.3.1
cycler==0.12.1
decorator==5.1.1
executing==2.1.0
Flask==3.1.0
fonttools==4.55.3
greenlet==3.1.1
idna==3.10
ipython==8.31.0
ipywidgets==8.1.5
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.5
joblib==1.4.2
jsonpickle==4.0.1
jupyterlab_widgets==3.0.13
kiwisolver==1.4.8
MarkupSafe==3.0.2
matplotlib==3.10.0
matplotlib-inline==0.1.7
numpy==2.2.1
packaging==24.2
pandas==2.2.3
parso==0.8.4
pexpect==4.9.0
pillow==11.0.0
prompt_toolkit==3.0.48
ptyprocess==0.7.0
pure_eval==0.2.3
pyaml==24.12.1
Pygments==2.18.0
pyparsing==3.2.0
python-dateutil==2.9.0.post0
pytz==2024.2
PyYAML==6.0.2
requests==2.32.3
scikit-learn==1.6.0
scipy==1.14.1
seaborn==0.13.2
six==1.17.0
SQLAlchemy==2.0.36
stack-data==0.6.3
threadpoolctl==3.5.0
toml==0.10.2
tqdm==4.67.1
traitlets==5.14.3
typing_extensions==4.12.2
tzdata==2024.2
urllib3==2.3.0
wcwidth==0.2.13
Werkzeug==3.1.3
widgetsnbextension==4.0.13
yo_fluq_ds==2.0.5
"""

if __name__ == '__main__':
    create_brainbox_builder().build_image('brainbox', LocalExecutor())