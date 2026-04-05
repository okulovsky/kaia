from dataclasses import dataclass
from datetime import datetime
from unittest import TestCase

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from brainbox.framework.job_processing.core.job import Job, BrainBoxBase
from brainbox.framework.app.tasks.api import TasksApi


def _engine():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    BrainBoxBase.metadata.create_all(engine)
    return engine


T0 = datetime(2024, 1, 1, 12, 0, 0)


def _finished_job(id, result):
    return Job(
        id=id,
        decider='D',
        batch=id,
        arguments={},
        has_dependencies=False,
        received_timestamp=T0,
        finished_timestamp=T0,
        success=True,
        result=result,
    )


def _failed_job(id, error):
    return Job(
        id=id,
        decider='D',
        batch=id,
        arguments={},
        has_dependencies=False,
        received_timestamp=T0,
        finished_timestamp=T0,
        success=False,
        error=error,
    )


# --- types used in round-trip tests ---

@dataclass
class SampleDataclass:
    name: str
    value: int
    score: float


class SampleClass:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, SampleClass) and self.x == other.x and self.y == other.y


class TestGetResultPrimitives(TestCase):
    """Primitive Python types survive the result round-trip"""

    def test_int(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', 42))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual(42, api.get_result('j1'))

    def test_float(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', 3.14))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertAlmostEqual(3.14, api.get_result('j1'))

    def test_string(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', 'hello world'))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual('hello world', api.get_result('j1'))

    def test_none(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', None))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertIsNone(api.get_result('j1'))

    def test_bool(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', True))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual(True, api.get_result('j1'))


class TestGetResultCollections(TestCase):
    """Collection types survive the result round-trip"""

    def test_list_of_ints(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', [1, 2, 3]))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual([1, 2, 3], api.get_result('j1'))

    def test_list_of_strings(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', ['a', 'b', 'c']))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual(['a', 'b', 'c'], api.get_result('j1'))

    def test_dict(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', {'key': 'value', 'n': 99}))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual({'key': 'value', 'n': 99}, api.get_result('j1'))

    def test_bytes(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_finished_job('j1', b'\x00\x01\x02'))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual(b'\x00\x01\x02', api.get_result('j1'))


class TestGetResultDataclass(TestCase):
    """Dataclass instances survive the result round-trip"""

    def test_simple_dataclass(self):
        engine = _engine()
        original = SampleDataclass(name='test', value=7, score=0.9)
        with Session(engine) as s:
            s.add(_finished_job('j1', original))
            s.commit()
        with TasksApi.test(engine) as api:
            result = api.get_result('j1')
        self.assertIsInstance(result, SampleDataclass)
        self.assertEqual('test', result.name)
        self.assertEqual(7, result.value)
        self.assertAlmostEqual(0.9, result.score)

    def test_list_of_dataclasses(self):
        engine = _engine()
        originals = [SampleDataclass(name=f'item{i}', value=i, score=i * 0.1) for i in range(3)]
        with Session(engine) as s:
            s.add(_finished_job('j1', originals))
            s.commit()
        with TasksApi.test(engine) as api:
            result = api.get_result('j1')
        self.assertEqual(3, len(result))
        self.assertIsInstance(result[0], SampleDataclass)
        self.assertEqual('item2', result[2].name)


class TestGetResultPlainClass(TestCase):
    """Plain (non-dataclass) class instances survive the result round-trip via pickle"""

    def test_plain_class(self):
        engine = _engine()
        original = SampleClass(x=10, y=20)
        with Session(engine) as s:
            s.add(_finished_job('j1', original))
            s.commit()
        with TasksApi.test(engine) as api:
            result = api.get_result('j1')
        self.assertIsInstance(result, SampleClass)
        self.assertEqual(original, result)

    def test_list_of_plain_classes(self):
        engine = _engine()
        originals = [SampleClass(x=i, y=i * 2) for i in range(4)]
        with Session(engine) as s:
            s.add(_finished_job('j1', originals))
            s.commit()
        with TasksApi.test(engine) as api:
            result = api.get_result('j1')
        self.assertEqual(4, len(result))
        self.assertEqual(SampleClass(x=3, y=6), result[3])


class TestGetResultErrors(TestCase):
    """get_result raises for unknown job IDs"""

    def test_unknown_id_raises(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            with self.assertRaises(Exception):
                api.get_result('no-such-id')
