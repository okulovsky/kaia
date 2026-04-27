from unittest import TestCase
from pathlib import Path
import tempfile
import os

from foundation_kaia.logging import Logger
from foundation_kaia.brainbox_utils.training import BrainboxReportItem, LongBrainboxProcess, logger


class SuccessProcess(LongBrainboxProcess[str]):
    def execute(self) -> str:
        logger.info("Step 1")
        logger.info("Step 2")
        return "done"


class FailingProcess(LongBrainboxProcess[str]):
    def execute(self) -> str:
        logger.info("Before error")
        raise ValueError("something went wrong")


class TestLongBrainboxProcess(TestCase):
    def test_successful_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "log.html")
            items = list(SuccessProcess().start_process(log_file))

            log_items = [i for i in items if i.log is not None]
            result_items = [i for i in items if i.result is not None]

            self.assertEqual(len(log_items), 2)
            self.assertEqual(log_items[0].log, "Step 1")
            self.assertEqual(log_items[1].log, "Step 2")
            self.assertEqual(len(result_items), 1)
            self.assertEqual(result_items[0].result, "done")

    def test_exception_propagation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "log.html")
            process = FailingProcess()
            result = []
            with self.assertRaises(ValueError) as ctx:
                for element in process.start_process(log_file):
                    result.append(element)

            self.assertIn("something went wrong", str(ctx.exception))
            self.assertEqual(2, len(result))
            self.assertEqual('Before error', result[0].log)
            self.assertIn('Traceback', result[1].log)

    def test_logging_writes_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "log.html")
            list(SuccessProcess().start_process(log_file))

            self.assertTrue(Path(log_file).exists())
            html = Path(log_file).read_text()
            self.assertIn("Step 1", html)
            self.assertIn("Step 2", html)
