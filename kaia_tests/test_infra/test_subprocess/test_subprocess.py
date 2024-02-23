from unittest import TestCase
from kaia.infra.handy_subprocess import *
from kaia.infra import Loc
import sys
from pathlib import Path
import subprocess



class SubProcessCallTestCase(TestCase):
    def test_call_normal_process(self):
        r = subprocess_call([sys.executable, Path(__file__).parent/'normal_process.py'])
        self.assertEqual(0, r.return_code)
        self.assertEqual('0 1 2 3 4 5 6 7 8 ', r.str_output)

    def test_call_err_process(self):
        r = subprocess_call([sys.executable, Path(__file__).parent/'err_process.py'])
        self.assertEqual(1, r.return_code)
        self.assertIn('Error4321', r.str_output)

    def test_input_process(self):
        r = subprocess_push_input([sys.executable, Path(__file__).parent/'input_process.py'], 'test\n')
        self.assertEqual(0, r.return_code)
        self.assertEqual('input was test', r.str_output)

    def test_input_process_err(self):
        r = subprocess_push_input([sys.executable, Path(__file__).parent/'input_process.py'], 'err')
        print(r)
        self.assertEqual(1, r.return_code)
        self.assertIn('Error5432', r.str_output)










