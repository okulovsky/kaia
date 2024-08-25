from kaia.brainbox.core import File, IDecider, BrainBoxTestApi, BrainBoxTask
from uuid import uuid4
from unittest import TestCase
from kaia.infra import FileIO

class Test(IDecider):
    def element(self, value: str):
        return File(str(uuid4()), value.encode('ascii'))

    def tuple(self, value: str):
        return (
            File(str(uuid4()), (value + '0').encode('ascii')),
            File(str(uuid4()), (value + '1').encode('ascii')),
            value
        )

    def list(self, value: str):
        return [
            File(str(uuid4()), (value + '0').encode('ascii')),
            File(str(uuid4()), (value + '1').encode('ascii')),
            value
        ]

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass


class FileAsDeciderReturnTestCase(TestCase):
    def check_file(self, api, obj, value):
        self.assertIsInstance(obj, File)
        self.assertIsNone(obj.content)
        result = FileIO.read_bytes(api.download(obj))
        self.assertEqual(value, result)



    def test_files_as_deciders_returned_value(self):
        services = dict(Test=Test())
        with BrainBoxTestApi(services) as api:
            result = api.execute(BrainBoxTask(decider=Test.element, arguments=dict(value='x')))
            self.check_file(api, result, b'x')

            result = api.execute(BrainBoxTask(decider=Test.list, arguments=dict(value='y')))
            self.assertIsInstance(result, list)
            self.check_file(api, result[0], b'y0')
            self.check_file(api, result[1], b'y1')
            self.assertEqual('y', result[2])

            result = api.execute(BrainBoxTask(decider=Test.tuple, arguments=dict(value='z')))
            self.assertIsInstance(result, tuple)
            self.check_file(api, result[0], b'z0')
            self.check_file(api, result[1], b'z1')
            self.assertEqual('z', result[2])


