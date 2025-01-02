from brainbox import BrainBox
from brainbox.deciders import Boilerplate
from unittest import TestCase
from brainbox.doc import run_all

class BoilerplateTestCase(TestCase):
    def test_boilerplate_scenario(self):
        with BrainBox.Api.Test() as api:
            run_all(api, self)

