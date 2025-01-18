from brainbox.framework.deployment import LocalExecutor, Command
import sys
from unittest import TestCase
from datetime import datetime

ERROR = (sys.executable,'-m','brainbox.tests.test_deployment.test_local_executor.error')
NOERROR = (sys.executable,'-m','brainbox.tests.test_deployment.test_local_executor.no_error')


class Monitor:
    def __init__(self):
        self.buffer = []
    def __call__(self, s):
        self.buffer.append((s,datetime.now()))

class LocalExecutorTestCase(TestCase):
    def test_no_output_handling_error(self):
        try:
            LocalExecutor().execute(ERROR, Command.Options())
            s = None
        except Exception as ex:
            s = str(ex)
        print(s)
        self.assertIsNotNone(s)

    def test_no_output_handling(self):
        self.assertIsNone(
            LocalExecutor().execute(ERROR, Command.Options(ignore_exit_code=True))
        )

        self.assertIsNone(
            LocalExecutor().execute(NOERROR)
        )



    def test_return_output_error(self):
        try:
            LocalExecutor().execute(ERROR, Command.Options(return_output=True))
            s = None
        except Exception as ex:
            s = str(ex)
        print(s)
        self.assertIsNotNone(s)
        self.assertIn('Traceback', s)

    def check(self, output, *control):
        lines = output.split('\n')[:len(control)]
        for expected, actual in zip(control, lines):
            actual = actual.replace('\r', '')
            self.assertEqual(expected, actual)

    def test_return_output(self):
        result = LocalExecutor().execute(ERROR, Command.Options(return_output=True, ignore_exit_code=True))
        self.check(result, 'STDOUT', 'STDERR', 'Traceback (most recent call last):')

        result = LocalExecutor().execute(NOERROR, Command.Options(return_output=True))
        self.check(result, 'STDOUT', 'STDERR', 'NO_ERROR')


    def test_monitoring_output_error(self):
        try:
            LocalExecutor().execute(ERROR, Command.Options(monitor_output=print))
            s = None
        except Exception as ex:
            s = str(ex)
        print(s)
        self.assertIsNotNone(s)
        self.assertIn('Traceback', s)
        self.assertNotIn('\n\n',s)

    def check_between(self, time_1, time_2, min, max):
        d = (time_2 - time_1).total_seconds()
        self.assertGreater(d, min)
        self.assertLess(d,max)



    def test_monitoring_output(self):
        monitor = Monitor()
        result = LocalExecutor().execute(NOERROR, Command.Options(monitor_output=monitor))
        self.check_between(monitor.buffer[0][1], monitor.buffer[1][1], 0.99, 1.01)
        self.check_between(monitor.buffer[1][1], monitor.buffer[2][1], 0.09, 0.11)
        self.check('\n'.join(z[0] for z in monitor.buffer), 'STDOUT', 'STDERR', 'NO_ERROR')
        self.check(result, 'STDOUT', 'STDERR', 'NO_ERROR')


    def test_monitoring_output_error_ignored(self):
        monitor = Monitor()
        result = LocalExecutor().execute(ERROR, Command.Options(monitor_output=monitor, ignore_exit_code=True))
        self.check('\n'.join(z[0] for z in monitor.buffer), 'STDOUT', 'STDERR', 'Traceback (most recent call last):')
        self.check(result, 'STDOUT', 'STDERR', 'Traceback (most recent call last):')




