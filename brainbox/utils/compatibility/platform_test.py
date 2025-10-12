import os
import time

from brainbox.framework.deployment import LocalExecutor
from brainbox.framework import DockerWebServiceController, BrainBoxApi, ApiUtils, ConnectionSettings, BrainboxImageBuilder
import subprocess

def test_on_arm64(controller: DockerWebServiceController, parameter: str = None):
    controller.get_deployment().stop().remove()

    subprocess.call([
        'docker',
        'run',
        '--privileged',
        '--rm',
        'tonistiigi/binfmt',
        '--install',
        'arm64'
    ])

    builder = controller.get_image_builder()
    if not isinstance(builder, BrainboxImageBuilder):
        raise ValueError("Can only test controllers that use BrainBoxImageBuidler")
    builder.build_command = ['buildx','build','--platform', 'linux/arm64', '--load']

    name = controller.get_snake_case_name()
    builder.build_image(name, LocalExecutor())


    configuration = controller.get_service_run_configuration(parameter)
    configuration.platform = 'linux/arm64'

    controller.run_with_configuration(configuration)

    settings: ConnectionSettings = controller.settings.connection

    print('CONTAINED IS UP. WAITING FOR SERVER')

    ApiUtils.wait_for_reply(f'http://127.0.0.1:{settings.port}', 1000)

    print('SERVER IS RUNNING. STARTING TEST')

    with BrainBoxApi.Test(always_on_planner=True) as api:
        controller.self_test(api = api)



