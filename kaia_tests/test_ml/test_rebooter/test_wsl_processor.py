import threading
from threading import Thread
from kaia.ml.rebooter import WslProcessController
from unittest import TestCase
import time

class WslTestCase(TestCase):
    def test_wsl_processor(self):
        processor = WslProcessController(
            '''~/anaconda3/bin/python -c "import time; \nfor i in range(10): print(i, end='')"''',
        )
        processor.start()
        output = processor.get_output()
        self.assertEqual('0123456789', output.strip())

    def test_wsl_processor_termination(self):
        processor = WslProcessController(
            '''~/anaconda3/bin/python -c "import time\nfor i in range(10000): print(i, end='');"''',
        )
        thread = Thread(target=processor.start)
        thread.start()
        time.sleep(0.1)
        processor.terminate(thread)
        output = processor.get_output().strip()
        self.assertGreater(len(output), 0)
        self.assertTrue(output.startswith('0123456789'))

