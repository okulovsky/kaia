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


def _job(id, batch='b1', decider='D', method=None,
         received=None, accepted=None, finished=None,
         success=False, progress=None, error=None):
    return Job(
        id=id,
        batch=batch,
        decider=decider,
        method=method,
        arguments={},
        has_dependencies=False,
        received_timestamp=received or T0,
        accepted_timestamp=accepted,
        finished_timestamp=finished,
        success=success,
        progress=progress,
        error=error,
    )


def _service(engine):
    return JobsService(engine, CommandQueue())


class TestStatusDerivation(TestCase):
    """status field is derived from timestamp/success combination"""

    def test_waiting(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1'))
            s.commit()
        records = _service(engine).get_jobs('b1')
        self.assertEqual('waiting', records[0].status)

    def test_in_work(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', accepted=T0 + timedelta(seconds=5)))
            s.commit()
        records = _service(engine).get_jobs('b1')
        self.assertEqual('in_work', records[0].status)

    def test_success(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', accepted=T0, finished=T0 + timedelta(seconds=10), success=True))
            s.commit()
        records = _service(engine).get_jobs('b1')
        self.assertEqual('success', records[0].status)

    def test_failure(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', accepted=T0, finished=T0 + timedelta(seconds=10), success=False))
            s.commit()
        records = _service(engine).get_jobs('b1')
        self.assertEqual('failure', records[0].status)


class TestTimingFields(TestCase):
    """in_queue and in_work are computed in Python from timestamps"""

    def test_in_queue_none_when_not_accepted(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1'))
            s.commit()
        record = _service(engine).get_jobs('b1')[0]
        self.assertIsNone(record.in_queue)
        self.assertIsNone(record.in_work)

    def test_in_queue_computed_when_accepted(self):
        engine = _engine()
        accepted = T0 + timedelta(seconds=15)
        with Session(engine) as s:
            s.add(_job('j1', accepted=accepted))
            s.commit()
        record = _service(engine).get_jobs('b1')[0]
        self.assertAlmostEqual(15.0, record.in_queue, places=1)

    def test_in_work_computed_when_finished(self):
        engine = _engine()
        accepted = T0 + timedelta(seconds=5)
        finished = T0 + timedelta(seconds=25)
        with Session(engine) as s:
            s.add(_job('j1', accepted=accepted, finished=finished, success=True))
            s.commit()
        record = _service(engine).get_jobs('b1')[0]
        self.assertAlmostEqual(20.0, record.in_work, places=1)

    def test_in_work_running_when_not_yet_finished(self):
        engine = _engine()
        accepted = T0
        with Session(engine) as s:
            s.add(_job('j1', accepted=accepted))
            s.commit()
        record = _service(engine).get_jobs('b1')[0]
        # in_work measured against datetime.now(), so just check it's positive
        self.assertIsNotNone(record.in_work)
        self.assertGreater(record.in_work, 0.0)


class TestDeciderLabel(TestCase):
    """decider field uses 'decider:method' when method is set"""

    def test_no_method(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', decider='Whisper'))
            s.commit()
        record = _service(engine).get_jobs('b1')[0]
        self.assertEqual('Whisper', record.decider)

    def test_with_method(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', decider='LLM', method='chat'))
            s.commit()
        record = _service(engine).get_jobs('b1')[0]
        self.assertEqual('LLM:chat', record.decider)


class TestFiltering(TestCase):
    """get_jobs only returns jobs belonging to the requested batch"""

    def test_only_requested_batch_returned(self):
        engine = _engine()
        with Session(engine) as s:
            s.add_all([
                _job('j1', batch='b1'),
                _job('j2', batch='b2'),
                _job('j3', batch='b1'),
            ])
            s.commit()
        records = _service(engine).get_jobs('b1')
        self.assertEqual(2, len(records))
        self.assertTrue(all(r.batch == 'b1' for r in records))

    def test_empty_result_for_unknown_batch(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', batch='b1'))
            s.commit()
        records = _service(engine).get_jobs('no-such-batch')
        self.assertEqual([], records)


class TestOrdering(TestCase):
    """Results are sorted newest-received first"""

    def test_newest_first(self):
        engine = _engine()
        with Session(engine) as s:
            s.add_all([
                _job('j1', received=T0),
                _job('j2', received=T0 + timedelta(seconds=10)),
                _job('j3', received=T0 + timedelta(seconds=5)),
            ])
            s.commit()
        ids = [r.id for r in _service(engine).get_jobs('b1')]
        self.assertEqual(['j2', 'j3', 'j1'], ids)


class TestTrivialFields(TestCase):
    """id, batch, timestamps, progress, error are passed through unchanged"""

    def test_fields_passthrough(self):
        engine = _engine()
        accepted = T0 + timedelta(seconds=3)
        finished = T0 + timedelta(seconds=8)
        with Session(engine) as s:
            s.add(_job('job-abc', batch='batch-xyz', decider='D',
                       received=T0, accepted=accepted, finished=finished,
                       success=True, progress=0.75, error=None))
            s.commit()
        r = _service(engine).get_jobs('batch-xyz')[0]
        self.assertEqual('job-abc', r.id)
        self.assertEqual('batch-xyz', r.batch)
        self.assertEqual(T0, r.received_timestamp)
        self.assertEqual(accepted, r.accepted_timestamp)
        self.assertEqual(finished, r.finished_timestamp)
        self.assertEqual(0.75, r.progress)
        self.assertIsNone(r.error)


class TestCancelJob(TestCase):
    def test_cancel_enqueues_cancel_action_with_correct_job_id(self):
        engine = _engine()
        queue = CommandQueue()
        service = JobsService(engine, queue)

        service.cancel_job('job-xyz')

        self.assertEqual(1, queue.qsize())
        action = queue.get_nowait()
        self.assertIsInstance(action, CancelAction)
        self.assertEqual('job-xyz', action.cancel_job_id)
        self.assertIsNone(action.cancel_batch_id)
