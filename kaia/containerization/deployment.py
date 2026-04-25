from brainbox.framework.deployment import Machine, IImageBuilder, IContainerRunner, Deployment, SSHExecutor, RsyncImageSource, LocalExecutor
from pathlib import Path
import os
from foundation_kaia.misc import Loc

def get_remote_machine() -> Machine:
    return Machine(
        int(os.environ['SERVER_USER_ID']),
        int(os.environ['SERVER_USER_ID']),
        os.environ['SERVER_IP_ADDRESS'],
        os.environ['SERVER_USERNAME']
    )

def get_remote_working_directory() -> Path:
    return Path(os.environ['SERVER_WORKING_DIRECTORY'])

def get_deployment(
        name: str,
        image_builder: IImageBuilder,
        runner: IContainerRunner,
):
    remote_working_directory = get_remote_working_directory()
    remote_machine = get_remote_machine()
    return Deployment(
        source = RsyncImageSource(
            name,
            Loc.temp_folder/'docker_cache'/name,
            str(remote_working_directory/'docker_cache'/name),
            remote_machine
        ),
        runner = runner,
        builder = image_builder,
        executor = SSHExecutor(remote_machine),
        build_executor=LocalExecutor()
    )