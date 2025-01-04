from kaia.common import Loc
from unittest import TestCase
from kaia.demo import *

class TestSetup:
    def __init__(self, tc: TestCase):
        self.tc = tc

    def __enter__(self):
        self.test_folder = Loc.create_test_folder()
        folder = self.test_folder.__enter__()
        app = KaiaApp(folder)
        set_brainbox_service_and_api(app)
        set_avatar_service_and_api(app)
        set_web_service_and_api(app)
        set_core_service(app)
        self.tester = KaiaAppTester(app, self.tc)
        return self.tester.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tester.__exit__(exc_type, exc_val, exc_tb)
        self.test_folder.__exit__(exc_type, exc_val, exc_tb)



