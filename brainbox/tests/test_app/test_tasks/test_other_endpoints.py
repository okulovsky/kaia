from datetime import datetime
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from brainbox.framework.job_processing.core.job import Job, BrainBoxBase
from brainbox.framework.app.tasks.api import TasksApi
from brainbox.framework.app.tasks.dto import JobSummary


T0 = datetime(2024, 1, 1, 12, 0, 0)
T1 = datetime(2024, 1, 1, 12, 0, 5)


def _engine():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    BrainBoxBase.metadata.create_all(engine)
    return engine


def _job(id='j1', decider='Whisper', parameter=None, method=None, batch=None,
         arguments=None, info=None, log=None, error=None,
         finished_timestamp=None, success=False):
    return Job(
        id=id,
        decider=decider,
        parameter=parameter,
        method=method,
        batch=batch or id,
        arguments=arguments or {},
        info=info,
        log=log,
        error=error,
        has_dependencies=False,
        received_timestamp=T0,
        finished_timestamp=finished_timestamp,
        success=success,
    )


class TestGetJob(TestCase):
    def test_returns_correct_job(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', decider='LLM', method='chat'))
            s.commit()
        with TasksApi.test(engine) as api:
            job = api.get_job('j1')
        self.assertEqual('j1', job.id)
        self.assertEqual('LLM', job.decider)
        self.assertEqual('chat', job.method)

    def test_unknown_id_raises(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            with self.assertRaises(Exception):
                api.get_job('no-such-id')


class TestGetJobSummary(TestCase):
    def test_returns_job_summary(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', decider='Whisper', method='transcribe',
                       finished_timestamp=T1, success=True))
            s.commit()
        with TasksApi.test(engine) as api:
            summary = api.get_job_summary('j1')
        self.assertIsInstance(summary, JobSummary)
        self.assertEqual('j1', summary.id)
        self.assertEqual('Whisper', summary.decider)
        self.assertEqual('transcribe', summary.method)
        self.assertTrue(summary.finished)
        self.assertTrue(summary.success)

    def test_not_finished_job(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1'))
            s.commit()
        with TasksApi.test(engine) as api:
            summary = api.get_job_summary('j1')
        self.assertFalse(summary.finished)
        self.assertFalse(summary.success)

    def test_unknown_id_raises(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            with self.assertRaises(Exception):
                api.get_job_summary('no-such-id')


class TestGetInfo(TestCase):
    def test_returns_info(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', info={'source': 'mic', 'lang': 'en'}))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual({'source': 'mic', 'lang': 'en'}, api.get_info('j1'))

    def test_none_info(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', info=None))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertIsNone(api.get_info('j1'))

    def test_unknown_id_raises(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            with self.assertRaises(Exception):
                api.get_info('no-such-id')


class TestGetError(TestCase):
    def test_returns_error_message(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', error='something went wrong', finished_timestamp=T1))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual('something went wrong', api.get_error('j1'))

    def test_none_when_no_error(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1'))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertIsNone(api.get_error('j1'))

    def test_unknown_id_raises(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            with self.assertRaises(Exception):
                api.get_error('no-such-id')


class TestGetLog(TestCase):
    def test_returns_log_entries(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', log=['step 1', 'step 2', 'done']))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertEqual(['step 1', 'step 2', 'done'], api.get_log('j1'))

    def test_none_when_no_log(self):
        engine = _engine()
        with Session(engine) as s:
            s.add(_job('j1', log=None))
            s.commit()
        with TasksApi.test(engine) as api:
            self.assertIsNone(api.get_log('j1'))

    def test_unknown_id_raises(self):
        engine = _engine()
        with TasksApi.test(engine) as api:
            with self.assertRaises(Exception):
                api.get_log('no-such-id')
