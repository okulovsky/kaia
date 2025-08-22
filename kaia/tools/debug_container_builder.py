from brainbox.framework import deployment as d
from foundation_kaia.misc import Loc
from yo_fluq import Query

def create_builder():

    dependencies = (
        Query.file.text(Loc.root_folder/'requirements.txt')
        .where(lambda z: not z.startswith('#') and 'pyaudio' not in z)
        .to_list()
    )

    folders = ['foundation_kaia', 'brainbox', 'eaglesong', 'grammatron', 'avatar', 'phonix', 'kaia']

    copy = {
        Loc.root_folder/name:name
        for name in list(folders)
    }

    builder = d.SmallImageBuilder(
        Loc.temp_folder/'deployments/avatar-debug-server',
        DOCKERFILE,
        dependencies,
        add_current_user=True,
        copy_to_code_path=copy,
        write_to_code_path={
            'pyproject.toml': TOML
        },
    )

    return builder



DOCKERFILE = f'''
FROM python:3.11

{{{d.SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{d.SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . /home/app

WORKDIR /home/app

RUN pip freeze

RUN pip install --user -e .

ENTRYPOINT ["python", "-m", "kaia.tools.debug_container_entry_point"]
'''


TOML = '''
[project]
name="kaia"
version="0.0.0"

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]

'''