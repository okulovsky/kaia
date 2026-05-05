from unittest import TestCase
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from brainbox.framework.job_processing.core.job import Job, BrainBoxBase
from brainbox.framework.job_processing.main_loop import CancelAction, CommandQueue
from brainbox.framework.app.jobs.service import JobsService


def _engine():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False})
    BrainBoxBase.metadata.create_all(engine)
    return engine


T0 = datetime(2024, 1, 1, 12, 0, 0)


def _job(id, batch='b1', decider='D', method=None, received=None):
    return Job(
        id=id,
        batch=batch,
        decider=decider,
        method=method,
        arguments={},
        has_dependencies=False,
        received_timestamp=received or T0,
    )


def _service(engine):
    return JobsService(engine, CommandQueue())


class TestGetJobsOrdering(TestCase):
    """get_jobs yields jobs in the same order as the input ids, regardless of DB order"""

    def test_order_matches_input(self):
        engine = _engine()
        with Session(engine) as s:
            s.add_all([
                _job('j1', received=T0),
                _job('j2', received=T0 + timedelta(seconds=10)),
                _job('j3', received=T0 + timedelta(seconds=5)),
            ])
            s.commit()

        result = list(_service(engine).get_jobs(['j3', 'j1', 'j2']))
        self.assertEqual(['j3', 'j1', 'j2'], [j.id for j in result])

    def test_raises_for_unknown_id(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1'))
            s.commit()

        with self.assertRaises(ValueError):
            list(_service(engine).get_jobs(['j1', 'no-such-id']))


class TestGetJobSummariesOrdering(TestCase):
    """get_job_summaries returns summaries in the same order as the input ids"""

    def test_order_matches_input(self):
        engine = _engine()
        with Session(engine) as s:
            s.add_all([
                _job('j1', received=T0),
                _job('j2', received=T0 + timedelta(seconds=10)),
                _job('j3', received=T0 + timedelta(seconds=5)),
            ])
            s.commit()

        summaries = _service(engine).get_job_summaries(['j3', 'j1', 'j2'])
        self.assertEqual(['j3', 'j1', 'j2'], [s.id for s in summaries])

    def test_fields_passed_through(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', decider='Whisper', method='transcribe'))
            s.commit()

        s = _service(engine).get_job_summaries(['j1'])[0]
        self.assertEqual('j1', s.id)
        self.assertEqual('Whisper', s.decider)
        self.assertEqual('transcribe', s.method)


class TestCancelJob(TestCase):
    def test_cancel_enqueues_action_with_correct_job_id(self):
        engine = _engine()
        queue = CommandQueue()
        JobsService(engine, queue).cancel_job('job-xyz')

        self.assertEqual(1, queue.qsize())
        action = queue.get_nowait()
        self.assertIsInstance(action, CancelAction)
        self.assertEqual('job-xyz', action.cancel_job_id)
        self.assertIsNone(action.cancel_batch_id)
