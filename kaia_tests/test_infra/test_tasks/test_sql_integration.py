from kaia.infra.tasks import *
from kaia.infra.sql_messenger import MessengerQuery
from kaia.zoo import Waiting
from unittest import TestCase
from kaia_tests.test_infra.test_tasks.integration_test_scenarios import *
import time
import pandas as pd

class SqlMultiprocTestCase(TestCase):
    def test_normal_run_in_multiprocess(self):
        waiting = Waiting(0.1)
        cycle = TaskCycle(waiting, 0.1)
        proc = SqlMultiprocTaskProcessor(cycle)
        two_requests_without_abort(self, proc)


    def test_abort_in_multiprocess(self):
        waiting = Waiting(0.1)
        cycle = TaskCycle(waiting, 0.1)
        proc = SqlMultiprocTaskProcessor(cycle)
        two_requests_one_is_aborted(self, proc)

    def test_normal_run_in_subprocess(self):
        cfg = SubprocessConfig('kaia.zoo.waiting:Waiting',[0.1],sleep=0.1)
        proc = SqlSubprocTaskProcessor(cfg)
        two_requests_without_abort(self, proc)


    def test_abort_in_subprocess(self):
        waiting = Waiting(0.1)
        cycle = TaskCycle(waiting, 0.1)
        proc = SqlMultiprocTaskProcessor(cycle)
        two_requests_one_is_aborted(self, proc)


