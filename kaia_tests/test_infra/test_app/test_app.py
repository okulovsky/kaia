import os

from kaia.infra.loc import Loc
from kaia.infra.comm import Sql
from kaia.infra.app import KaiaApp, SubprocessRunner
import time
from unittest import TestCase


def get_path():
    path = Loc.temp_folder/'tests/app_test/app_test'
    os.makedirs(path.parent, exist_ok=True)
    return path

def send():
    messenger = Sql().file(get_path()).messenger()
    ids = [messenger.add(None) for _ in range(10)]
    for i in range(10):
        left_open = messenger.Query(open=True).query_count(messenger)
        if left_open == 0:
            return
        time.sleep(0.1)
    raise ValueError('Test fails, waiting too long')

def receive():
    messenger = Sql().file(get_path()).messenger()
    while True:
        messenger.read_all_and_close()
        time.sleep(0.1)


class AppTestCase(TestCase):
    def test_multiprocess(self):
        if Loc.is_windows:
            self.skipTest('Not running under Windows')
        app = KaiaApp()
        app.add_multiproc_service(receive)
        app.set_primary_service(send)
        app.run()

    def test_subprocess(self):
        app = KaiaApp()
        app.add_subproc_service(receive)
        app.set_primary_service(send)
        app.run()

    def test_subprocess_exits(self):
        runner = SubprocessRunner(KaiaApp.run_forever)
        runner.run()
        time.sleep(0.5)
        runner.stop()


