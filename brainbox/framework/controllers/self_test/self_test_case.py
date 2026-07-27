from __future__ import annotations
from typing import Any, Callable, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from unittest import TestCase
from .last_call import LastCallDocumentation
from foundation_kaia.misc import Loc
from foundation_kaia.marshalling import File
import json

if TYPE_CHECKING:
    from brainbox.framework import BrainBoxApi


def check_if_its_sound(content, tc: TestCase):
    import soundfile as sf
    with Loc.create_test_file() as tmp_filename:
        with open(tmp_filename, "wb") as f:
            f.write(content)
        f = sf.SoundFile(tmp_filename)
        duration = f.frames / f.samplerate
        tc.assertGreater(duration, 1)
    f.close()


def check_if_its_image(content, tc: TestCase):
    from PIL import Image
    from io import BytesIO
    img = Image.open(BytesIO(content))
    tc.assertGreater(img.width, 0)
    tc.assertGreater(img.height, 0)


@dataclass
class SelfTestCase:
    class FileType(Enum):
        Image = 1
        Sound = 2

    task: Any
    condition: Optional[Callable[[Any, BrainBoxApi, TestCase], Any]] = None
    title: str|None = None
    file_type: Optional['SelfTestCase.FileType'] = None

    def execute(self, api: BrainBoxApi, test_case: TestCase|None = None) -> LastCallDocumentation:
        result = api.execute(self.task)
        if test_case is not None:
            if self.condition is not None:
                self.condition(result, api, test_case)
            if self.file_type == SelfTestCase.FileType.Image:
                SelfTestCase.assertFileIsImage()(result, api, test_case)
            elif self.file_type == SelfTestCase.FileType.Sound:
                SelfTestCase.assertFileIsSound()(result, api, test_case)
        documentation = api.last_call()
        if documentation.result is not None and documentation.result.file is not None:
            if self.file_type == SelfTestCase.FileType.Image:
                documentation.result.file.kind = File.Kind.Image
            elif self.file_type == SelfTestCase.FileType.Sound:
                documentation.result.file.kind = File.Kind.Audio
        return documentation

    @staticmethod
    def assertEqual(value: Any):
        def _(result, api: BrainBoxApi, test_case: TestCase|None = None):
            test_case.assertEqual(value, result)
        return _

    @staticmethod
    def assertFileContentEqual(value: bytes):
        def _(result, api: BrainBoxApi, test_case: TestCase|None = None):
            test_case.assertEqual(value, api.cache.read_file(result).content)
        return _

    @staticmethod
    def assertFileJsonEqual(value: Any):
        def _(result, api: BrainBoxApi, test_case: TestCase|None = None):
            test_case.assertEqual(value, json.loads(api.cache.read_file(result).content))
        return _

    @staticmethod
    def assertFileIsSound():
        return lambda result, api, test_case: check_if_its_sound(api.cache.read(result), test_case)

    @staticmethod
    def assertFileIsImage():
        return lambda result, api, test_case: check_if_its_image(api.cache.read(result), test_case)
