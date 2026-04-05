
from io import BytesIO
from unittest import TestCase

from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from brainbox.framework.app.api import BrainBoxApi
from brainbox.framework.controllers.self_test.last_call import LastCallDocumentation
from foundation_kaia.misc import Loc

PORT = 18196
_CONTENT = b'1222'
_EXPECTED_RESULT = [0, 1, 3, 0, 0, 0, 0, 0, 0, 0]


def _check_arg_file(tc: TestCase, api: BrainBoxApi, expected_content: bytes) -> None:
    doc: LastCallDocumentation = api.last_call()
    arg = doc.arguments['file']
    tc.assertIsNone(arg.error, msg=f"File conversion error: {arg.error}")
    tc.assertIsNotNone(arg.file)
    tc.assertEqual(expected_content, arg.file.content)


def _check_result_file(tc: TestCase, api: BrainBoxApi) -> None:
    doc: LastCallDocumentation = api.last_call()
    tc.assertIsNone(doc.result.error, msg=f"Result file conversion error: {doc.result.error}")
    tc.assertIsNotNone(doc.result.file)
    tc.assertGreater(len(doc.result.file.content), 0)


class LastCallFileLikeTestCase(TestCase):
    """Tests that FileLike arguments are correctly captured in last_call()."""

    def test_arguments(self):
        with BrainBoxApi.test([HelloBrainBox], port=PORT) as api:
            result = api.execute(HelloBrainBox.new_task().voice_embedding(_CONTENT))
            self.assertEqual(_EXPECTED_RESULT, result)
            _check_arg_file(self, api, _CONTENT)

            result = api.execute(HelloBrainBox.new_task().voice_embedding(BytesIO(_CONTENT)))
            self.assertEqual(_EXPECTED_RESULT, result)
            _check_arg_file(self, api, _CONTENT)

            with Loc.create_test_folder() as folder:
                path = folder / 'test_input.bin'
                path.write_bytes(_CONTENT)
                result = api.execute(HelloBrainBox.new_task().voice_embedding(str(path)))
                self.assertEqual(_EXPECTED_RESULT, result)
                _check_arg_file(self, api, _CONTENT)

                result = api.execute(HelloBrainBox.new_task().voice_embedding(path))
                self.assertEqual(_EXPECTED_RESULT, result)
                _check_arg_file(self, api, _CONTENT)

            api.cache.upload('test_input.bin', _CONTENT)
            result = api.execute(HelloBrainBox.new_task().voice_embedding('test_input.bin'))
            self.assertEqual(_EXPECTED_RESULT, result)
            _check_arg_file(self, api, _CONTENT)

    def test_result(self):
        # voiceover -> FileLike -> ResultType.BinaryFile
        with BrainBoxApi.test([HelloBrainBox], port=PORT) as api:
            api.execute(HelloBrainBox.new_task().voiceover('test'))
            _check_result_file(self, api)

            api.execute(HelloBrainBox.new_task().stream_voiceover([dict(text='a'), dict(text='b')]))
            _check_result_file(self, api)

            api.execute(HelloBrainBox.new_task().training(b'abcd'))
            _check_result_file(self, api)
