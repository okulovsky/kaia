import os
from brainbox.deciders import HelloBrainBox
from brainbox.framework import logger
from brainbox.framework.common import Loc, FileIO
from foundation_kaia.logging.simple import ExceptionItem, LineItem
from unittest import TestCase


class ErroneousHelloBrainBoxController(HelloBrainBox.Controller):
    def custom_self_test(self, api, tc: None|TestCase = None):
        logger.info("Some content")
        raise ValueError("Something has happened")


class ErroneousSelfTestReport(TestCase):
    def test_erroneous_report(self):
        controller = ErroneousHelloBrainBoxController()
        path = Loc.self_test_path / 'ErroneousHelloBrainBox'
        if path.is_file():
            os.unlink(path)
        try:
            controller.self_test()
        except:
            pass
        self.assertTrue(path.is_file())
        items = FileIO.read_pickle(path)
        self.assertIsInstance(items, list)
        self.assertTrue(any(isinstance(item, LineItem) and 'Some content' in item.to_string() for item in items))
        self.assertTrue(any(isinstance(item, ExceptionItem) for item in items))
