import os
from typing import Iterable

from brainbox.deciders import HelloBrainBox
from brainbox.framework import logger, BrainBoxLocations, SelfTestCase
from brainbox.framework.common import FileIO
from foundation_kaia.logging.simple import ExceptionItem, LineItem
from unittest import TestCase
import traceback


class ErroneousCustomHelloBrainBoxController(HelloBrainBox.Controller):
    def self_test_cases(self) -> Iterable[SelfTestCase]:
        return []

    def custom_self_test(self, api, tc: None|TestCase = None):
        logger.info("Some content")
        raise ValueError("Something has happened")


class ErroneousCaseHelloBrainBoxController(HelloBrainBox.Controller):
    def self_test_cases(self) -> Iterable[SelfTestCase]:
        return [
            SelfTestCase(
                HelloBrainBox.new_task().sum(2,2),
                lambda result, _, tc: tc.assertEqual(5, result)
            )
        ]

    def custom_self_test(self, api, tc: None|TestCase = None):
        pass



class ErroneousSelfTestReport(TestCase):
    def test_error_in_custom_report(self):
        controller = ErroneousCustomHelloBrainBoxController()
        path = BrainBoxLocations.default_self_tests_folder() / 'ErroneousCustomHelloBrainBox'
        if path.is_file():
            os.unlink(path)
        try:
            controller.self_test()
        except Exception:
            traceback.print_exc()
        self.assertTrue(path.is_file())
        items = FileIO.read_pickle(path)
        self.assertIsInstance(items, list)
        self.assertTrue(any(isinstance(item, LineItem) and 'Some content' in item.to_string() for item in items))
        self.assertTrue(any(isinstance(item, ExceptionItem) for item in items))

    def test_error_in_case_report(self):
        controller = ErroneousCaseHelloBrainBoxController()
        path = BrainBoxLocations.default_self_tests_folder() / 'ErroneousCaseHelloBrainBox'
        if path.is_file():
            os.unlink(path)
        try:
            controller.self_test()
        except Exception:
            pass# traceback.print_exc()
        print(f"Expecting in {path}")
        self.assertTrue(path.is_file())
        items = FileIO.read_pickle(path)
        self.assertIsInstance(items, list)
        self.assertIsInstance(items[0], ExceptionItem)

