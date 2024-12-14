from kaia.brainbox.deployment import *
import time
import os
from yo_fluq_ds import *
from pathlib import Path
from kaia.kaia.server.test.run_test_3 import run_test_3 as entry_point
from kaia.infra import Loc
import toml

def get_deployment():
    tag = str(int(time.time()))
    source = DockerIOImageSource(
        name='kaia-test-server',
        docker_url=os.environ['DOCKER_URL'],
        login=os.environ['DOCKER_USERNAME'],
        password=os.environ['DOCKER_PASSWORD'],
    )

    with open(Loc.root_folder/'pyproject.toml') as file:
        project = toml.load(file)
    dependencies = [d.split(';')[0] for d in project['project']['dependencies'] if 'PyAudio' not in d and 'platform_system != "Linux"' not in d]

    container = FullRepoContainerBuilder(
        name = 'kaia-test-server',
        tag = tag,
        entry_point=entry_point,
        dependencies=dependencies,
        deployed_folders=['kaia', 'demos'],
        python_version='3.11',
        root_path=Loc.root_folder,
    )


    deployment = Deployment(
        source,
        None,
        None,
        container,
        LocalExecutor()
    )
    return deployment


if __name__ == '__main__':
    get_deployment().build().push()
