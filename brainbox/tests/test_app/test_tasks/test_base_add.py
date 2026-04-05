from unittest import TestCase

from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

from brainbox.framework.job_processing.core.job import Job, BrainBoxBase
from brainbox.framework.task import JobDescription
from brainbox.framework.app.tasks.api import TasksApi


def _engine():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    BrainBoxBase.metadata.create_all(engine)
    return engine


def _desc(id, decider='D', method=None, batch=None, arguments=None, info=None):
    return JobDescription(
        id=id,
        decider=decider,
        parameter=None,
        method=method,
        arguments=arguments or {},
        info=info,
        batch=batch,
        ordering_token=None,
        dependencies={},
    )


class TestBaseAddIds(TestCase):
    """base_add returns the correct IDs in the same order as submitted"""

    def test_single_job_returns_one_id(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            ids = api.base_add([_desc('j1')])
        self.assertEqual(['j1'], ids)

    def test_multiple_jobs_return_all_ids_in_order(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            ids = api.base_add([_desc('j1'), _desc('j2'), _desc('j3')])
        self.assertEqual(['j1', 'j2', 'j3'], ids)


class TestBaseAddPersistence(TestCase):
    """Jobs submitted via base_add are actually written to the database"""

    def test_job_is_in_db_after_add(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            api.base_add([_desc('j1', decider='Whisper', method='transcribe')])
        with Session(engine) as s:
            job = s.scalar(select(Job).where(Job.id == 'j1'))
        self.assertIsNotNone(job)
        self.assertEqual('Whisper', job.decider)
        self.assertEqual('transcribe', job.method)

    def test_all_jobs_are_in_db(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            api.base_add([_desc('j1'), _desc('j2'), _desc('j3')])
        with Session(engine) as s:
            jobs = list(s.scalars(select(Job)))
        self.assertEqual(3, len(jobs))

    def test_received_timestamps_are_ordered(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            api.base_add([_desc('j1'), _desc('j2'), _desc('j3')])
        with Session(engine) as s:
            jobs = {j.id: j for j in s.scalars(select(Job))}
        self.assertLess(jobs['j1'].received_timestamp, jobs['j2'].received_timestamp)
        self.assertLess(jobs['j2'].received_timestamp, jobs['j3'].received_timestamp)

    def test_batch_defaults_to_own_id_when_not_set(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            api.base_add([_desc('j1', batch=None)])
        with Session(engine) as s:
            job = s.scalar(select(Job).where(Job.id == 'j1'))
        self.assertEqual('j1', job.batch)

    def test_explicit_batch_is_preserved(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            api.base_add([_desc('j1', batch='my-batch'), _desc('j2', batch='my-batch')])
        with Session(engine) as s:
            jobs = list(s.scalars(select(Job)))
        self.assertTrue(all(j.batch == 'my-batch' for j in jobs))


