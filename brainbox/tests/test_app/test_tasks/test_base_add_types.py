"""
Tests that arguments survive the full round-trip:
  client → HTTP → service → DB (PickleType) → DB query → and back via api.get_job(id).

Each test calls the shared helper _check(), which:
  1. calls base_add with the given arguments dict,
  2. reads the job back directly from the DB,
  3. reads the job back via api.get_job(id),
  4. asserts both match the original.

The datetime test is intentionally included to document/catch any
serialization issues with timestamps inside arguments.
"""
from dataclasses import dataclass
from datetime import datetime
from unittest import TestCase

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from brainbox.framework.job_processing.core.job import Job, BrainBoxBase
from brainbox.framework.task import JobDescription
from brainbox.framework.app.tasks.api import TasksApi


def _engine():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    BrainBoxBase.metadata.create_all(engine)
    return engine


def _desc(arguments):
    return JobDescription(
        id='j1',
        decider='D',
        parameter=None,
        method=None,
        arguments=arguments,
        info=None,
        batch=None,
        ordering_token=None,
        dependencies={},
    )


@dataclass
class Point:
    x: float
    y: float


class PlainPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, PlainPoint) and self.x == other.x and self.y == other.y


class TestArgumentTypes(TestCase):
    def _check(self, arguments: dict):
        engine = _engine()
        with TasksApi.test(engine) as api:
            api.base_add([_desc(arguments)])
            job_via_api = api.get_job('j1')
        with Session(engine) as s:
            job_via_db = s.scalar(select(Job).where(Job.id == 'j1'))
        self.assertEqual(arguments, job_via_db.arguments)
        self.assertEqual(arguments, job_via_api.arguments)

    def test_primitives(self):
        self._check({'n': 42, 'text': 'hello', 'flag': True, 'ratio': 0.5})

    def test_none_value(self):
        self._check({'optional': None})

    def test_list(self):
        self._check({'items': [1, 2, 3]})

    def test_nested_dict(self):
        self._check({'config': {'threshold': 0.5, 'tags': ['a', 'b']}})

    def test_dataclass(self):
        self._check({'point': Point(x=1.0, y=2.0)})

    def test_plain_class(self):
        self._check({'point': PlainPoint(x=3, y=4)})

    def test_datetime(self):
        # datetime is not JSON-serializable; this test documents whether it
        # survives the round-trip when stored in arguments (PickleType in DB,
        # but must also pass through the HTTP serialization layer).
        self._check({'ts': datetime(2024, 6, 1, 12, 0, 0)})
