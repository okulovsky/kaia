import os
from unittest import TestCase

from brainbox.deciders import Boilerplate
from brainbox.framework import TestReport
from brainbox.framework.common import Loc, FileIO
from unittest import TestCase



class ErroneousBoilerplateController(Boilerplate.Controller):
    def _self_test_internal(self, api, tc: None|TestCase = None) -> TestReport:
        yield TestReport.main_section_content("content")
        yield TestReport.section("Some section")
        raise ValueError("Something has happened")

class ErroneousSelfTestReport(TestCase):
    def test_erroneous_report(self):
        controller = ErroneousBoilerplateController()
        path = Loc.self_test_path/'ErroneousBoilerplate'
        if path.is_file():
            os.unlink(path)
        try:
            controller.self_test()
        except:
            pass
        self.assertTrue(path.is_file())
        report = FileIO.read_pickle(path)
        self.assertEqual(2, len(report.sections))
        self.assertEqual('ErroneousBoilerplate', report.name)
        self.assertIsNotNone(report.error)
