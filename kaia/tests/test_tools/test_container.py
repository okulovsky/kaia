from unittest import TestCase

import requests

from kaia.tools.debug_container_builder import create_builder
from brainbox.framework.deployment import LocalExecutor, DockerArgumentsHelper
from foundation_kaia.misc import Loc
import subprocess
from avatar.server import AvatarApi, AvatarStream, GenericMessage

class ContainerTestCase(TestCase):
    def test_container(self):
        builder = create_builder()
        builder.build_image('avatar-debug-server', LocalExecutor())
        web_folder = Loc.root_folder/'kaia/web'

        with Loc.create_test_folder() as cache_folder:
            arguments = [
                'docker',
                'run',
                '--rm',
                '--detach',
                *DockerArgumentsHelper.arg_mount_folders({
                    web_folder/'static': '/static',
                    web_folder/'scripts': '/scripts/compiled',
                    web_folder: '/index',
                    cache_folder: '/cache'
                }),
                *DockerArgumentsHelper.arg_publish_ports({
                    13002: 13002
                }),
                'avatar-debug-server',
            ]
            container = None
            try:
                container = subprocess.check_output(arguments, text=True).strip()
                print(container)

                api = AvatarApi('127.0.0.1:13002')
                api.wait()

                client = AvatarStream(api).create_client()
                client.put(GenericMessage(
                    payload=dict(test="Hello, world"),
                    message_type='MyType'
                ))

                data = client.pull()
                self.assertEqual(2, len(data))


                api.file_cache.upload(b'123456', 'test')
                self.assertEqual(
                    b'123456',
                    api.file_cache.download('test')
                )

                self.assertEqual(
                    200,
                    requests.get('http://127.0.0.1:13002/main').status_code
                )


            finally:
                if container is not None:
                    subprocess.call(['docker', 'stop', container])







