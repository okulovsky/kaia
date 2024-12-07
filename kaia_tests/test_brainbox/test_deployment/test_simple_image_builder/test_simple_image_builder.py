import os
from kaia.brainbox import deployment as d
from kaia.infra import FileIO, Loc
from pathlib import Path
import uuid
from unittest import TestCase

DOCKERFILE = f"""
FROM python:3.11

{{{d.SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{d.SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . /home/app/

ENTRYPOINT ["python", "/home/app/main.py"]
"""

data_folder = Path(__file__).parent / 'data'

class SimpleRun(d.IContainerRunner):
    def __init__(self, guid):
        self.guid=guid




    def run(self, image_name: str, container_name: str, executor: d.IExecutor):
        executor.create_empty_folder(data_folder)
        executor.execute([
            'docker',
            'run',
            d.Command.Comment("flags"),
            '--name', container_name,
            '-t',
            '--rm',
            '--mount', self.arg_mount(data_folder, '/home/app/data'),
            '--user', f'{executor.get_machine().user_id}:{executor.get_machine().user_id}',
            d.Command.Comment("image_name"),
            image_name,
            d.Command.Comment("command_line_arguments"),
            self.guid
        ])


class SimpleImageBuilderTestCase(TestCase):
    def test_simple_container_builder(self):
        id = str(uuid.uuid4())
        executor = d.LocalExecutor(True)
        builder = d.SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            ['pandas'],
            True
        )

        deployment = d.Deployment(
            d.LocalImageSource('test_image'),
            SimpleRun(id),
            executor,
            builder,
        )

        deployment.build().stop().remove().run()


        fname = data_folder/'test/test.txt'
        self.assertEqual('outer: '+id, FileIO.read_text(fname))

        if Loc.is_windows:
            self.skipTest('Windows')

        res = executor.execute(['ls','-l', fname.parent], d.Command.Options(return_output=True))
        res = res.decode('ascii').split('\n')[1]
        print(res)
        os.unlink(fname)
        self.assertNotIn('root', res)








