import unittest
from kaia.infra.tasks import TaskProcessor
import time
import pandas as pd

def two_requests_without_abort(self: unittest.TestCase, proc: TaskProcessor):
    proc.activate()
    id1 = proc.create_task(dict(ticks=4))
    id2 = proc.create_task(dict(ticks=2))
    time.sleep(1)
    pd.options.display.width = None
    pd.options.display.max_rows = None

    messages = proc.get_debug_messages_table()
    df = pd.DataFrame(messages)
    df = df.loc[df.tag_0!='is_alive']
    self.assertListEqual(
        ['null', '{"ticks": 4}', 'null', '{"ticks": 2}', 'null', '"Warmed up True"', '0.25', '"Tick 0/4"', '0.5',
         '"Tick 1/4"', '0.75', '"Tick 2/4"', '1.0', '"Tick 3/4"', 'null', '5', 'null', '"Warmed up True"', '0.5',
         '"Tick 0/2"', '1.0', '"Tick 1/2"', 'null', '3'],
        list(df.payload)
    )
    self.assertListEqual(
        ['received', 'arguments', 'received', 'arguments', 'accepted', 'log', 'progress', 'log', 'progress', 'log',
         'progress', 'log', 'progress', 'log', 'success', 'result', 'accepted', 'log', 'progress', 'log',
         'progress', 'log', 'success', 'result'],
        list(df.tag_0)
    )

    st1 = proc.get_status(id1)
    self.assertDictEqual(
        {'id': id1, 'received': True, 'arguments': {'ticks': 4},
         'accepted': True, 'progress': 1.0, 'aborted': False, 'success': True, 'failure': False, 'error': None,
         'log': ['Warmed up True', 'Tick 0/4', 'Tick 1/4', 'Tick 2/4', 'Tick 3/4'], 'result': 5},
        st1.__dict__
    )
    st2 = proc.get_status(id2)
    self.assertDictEqual(
        {'id': id2, 'received': True, 'arguments': {'ticks': 2},
         'accepted': True, 'progress': 1.0, 'aborted': False, 'success': True, 'failure': False, 'error': None,
         'log': ['Warmed up True', 'Tick 0/2', 'Tick 1/2'], 'result': 3},
        st2.__dict__
    )
    proc.deactivate()

def two_requests_one_is_aborted(self: unittest.TestCase, proc: TaskProcessor):
    proc.activate()
    id1 = proc.create_task(dict(ticks=4))
    id2 = proc.create_task(dict(ticks=2))
    time.sleep(0.2)
    proc.abort_task(id1)
    time.sleep(1)
    pd.options.display.width = None
    pd.options.display.max_rows = None

    messages = proc.get_debug_messages_table()
    df = pd.DataFrame(messages)
    print(df)
    df = df.loc[df.tag_0!='is_alive']
    self.assertGreaterEqual(df.loc[(df.tag_1 == id1) & (df.tag_0 == 'log')].shape[0], 2)
    self.assertEqual(1, df.loc[(df.tag_1 == id1) & (df.tag_0 == 'aborted')].shape[0])
    self.assertEqual(1, df.loc[(df.tag_1 == id1) & (df.tag_0 == 'error')].shape[0])
    st1 = proc.get_status(id1)
    self.assertTrue(st1.aborted)
    self.assertTrue(st1.failure)
    self.assertIsInstance(st1.error, dict)

    st2 = proc.get_status(id2)
    self.assertDictEqual(
        {'id': id2, 'received': True, 'arguments': {'ticks': 2}, 'accepted': True, 'progress': 1.0, 'aborted': False, 'success': True, 'failure': False, 'result': 3, 'error': None, 'log': ['Warmed up True', 'Tick 0/2', 'Tick 1/2']},
        st2.__dict__
    )
    proc.deactivate()


def is_alive(self: unittest.TestCase, proc: TaskProcessor):
    is_alive_1 = proc.is_alive(5)
    self.assertFalse(is_alive_1)
    proc.activate()
    time.sleep(1)
    is_alive_2 = proc.is_alive(5)
    self.assertTrue(is_alive_2)
    proc.deactivate()
