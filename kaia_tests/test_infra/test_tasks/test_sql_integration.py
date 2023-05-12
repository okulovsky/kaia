from kaia.infra import Loc
from kaia.infra.tasks import *
from unittest import TestCase
from kaia_tests.test_infra.test_tasks.integration_test_scenarios import *


class SqlMultiprocTestCase(TestCase):
    def test_normal_run_in_multiprocess(self):
        if Loc.is_windows:
            self.skipTest('Windows')
        waiting = Waiting(0.1)
        cycle = TaskCycle(waiting, 0.1)
        proc = SqlMultiprocTaskProcessor(cycle)
        two_requests_without_abort(self, proc)


    def test_abort_in_multiprocess(self):
        if Loc.is_windows:
            self.skipTest('Windows')
        waiting = Waiting(0.1)
        cycle = TaskCycle(waiting, 0.1)
        proc = SqlMultiprocTaskProcessor(cycle)
        two_requests_one_is_aborted(self, proc)

    def test_alive_in_multiprocess(self):
        if Loc.is_windows:
            self.skipTest('Windows')
        waiting = Waiting(0.1)
        cycle = TaskCycle(waiting, 0.1)
        proc = SqlMultiprocTaskProcessor(cycle)
        is_alive(self, proc)


    def test_normal_run_in_subprocess(self):
        cfg = SubprocessConfig('kaia.infra.tasks:Waiting',[0.1],sleep=0.1)
        proc = SqlSubprocTaskProcessor(cfg)
        two_requests_without_abort(self, proc)


    def test_abort_in_subprocess(self):
        cfg = SubprocessConfig('kaia.infra.tasks:Waiting', [0.1], sleep=0.1)
        proc = SqlSubprocTaskProcessor(cfg)
        two_requests_one_is_aborted(self, proc)

    def test_alive_in_subprocess(self):
        cfg = SubprocessConfig('kaia.infra.tasks.waiting:Waiting',[0.1],sleep=0.1)
        proc = SqlSubprocTaskProcessor(cfg)
        is_alive(self, proc)

    def test_multiproc_wont_run_in_windows(self):
        if not Loc.is_windows:
            self.skipTest('Linux')
        self.assertRaises(ValueError, lambda: SqlMultiprocTaskProcessor(TaskCycle(Waiting(0.1))))



