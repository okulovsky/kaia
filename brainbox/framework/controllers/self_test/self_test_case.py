from __future__ import annotations
from typing import Any, Callable, Optional, TYPE_CHECKING
from dataclasses import dataclass
from unittest import TestCase
from .last_call import LastCallDocumentation
from foundation_kaia.misc import Loc
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

@dataclass
class SelfTestCase:
    task: Any
    condition: Optional[Callable[[Any, BrainBoxApi, TestCase], Any]] = None
    title: str|None = None

    def execute(self, api: BrainBoxApi, test_case: TestCase|None = None) -> LastCallDocumentation:
        result = api.execute(self.task)
        if test_case is not None and self.condition is not None:
            self.condition(result, api, test_case)
        return api.last_call()

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
