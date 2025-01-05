from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase
from brainbox.doc import run_all

class ReadmeTestCase(TestCase):
    def test_readme(self):
        with BrainBox.Api.Test() as api:
            run_all(api, self)

