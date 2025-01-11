from brainbox.framework import File, BrainBoxApi, BrainBoxTask, IDecider, FileIO
from unittest import TestCase

from uuid import uuid4


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

    def dict(self, value: str):
        return {
            'file1': File(str(uuid4()), (value + '0').encode('ascii')),
            'file2': File(str(uuid4()), (value + '1').encode('ascii')),
            'value': value
        }

class FileAsDeciderReturnTestCase(TestCase):
    def check_file(self, api, obj, value):
        self.assertIsInstance(obj, str)
        result = FileIO.read_bytes(api.cache_folder/obj)
        self.assertEqual(value, result)

    def test_files_as_deciders_returned_value(self):
        with BrainBoxApi.ServerlessTest([Test()]) as api:
            result = api.execute(BrainBoxTask(decider=Test.element, arguments=dict(value='x')))
            self.check_file(api, result, b'x')

            result = api.execute(BrainBoxTask(decider=Test.list, arguments=dict(value='y')))
            self.assertIsInstance(result, list)
            self.check_file(api, result[0], b'y0')
            self.check_file(api, result[1], b'y1')
            self.assertEqual('y', result[2])

            result = api.execute(BrainBoxTask(decider=Test.dict, arguments=dict(value='u')))
            self.assertIsInstance(result, dict)
            self.check_file(api, result['file1'], b'u0')
            self.check_file(api, result['file2'], b'u1')
            self.assertEqual('u', result['value'])

            result = api.execute(BrainBoxTask(decider=Test.tuple, arguments=dict(value='z')))
            self.assertIsInstance(result, tuple)
            self.check_file(api, result[0], b'z0')
            self.check_file(api, result[1], b'z1')
            self.assertEqual('z', result[2])


