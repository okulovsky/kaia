from unittest import TestCase
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from brainbox.framework.job_processing.core.job import Job, BrainBoxBase
from brainbox.framework.job_processing.main_loop import CommandQueue
from brainbox.framework.app.batches import BatchesService


def _engine():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False})
    BrainBoxBase.metadata.create_all(engine)
    return engine


def _job(id, batch, decider, method=None,
         received=None, accepted=None, finished=None,
         success=False, progress=None):
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    return Job(
        id=id,
        batch=batch,
        decider=decider,
        method=method,
        arguments={},
        has_dependencies=False,
        received_timestamp=received or t0,
        accepted_timestamp=accepted,
        finished_timestamp=finished,
        success=success,
        progress=progress,
    )


def _service(engine):
    return BatchesService(engine, CommandQueue())


class TestDeciderAggregation(TestCase):
    """Decider labels: 'decider:method x N' grouping"""

    def test_single_decider_no_method(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'Whisper', received=t0),
                _job('j2', 'b1', 'Whisper', received=t0 + timedelta(seconds=1)),
            ])
            s.commit()

        result = _service(engine).get_batches()
        self.assertEqual(1, len(result.items))
        self.assertEqual(['Whisper x 2'], result.items[0].deciders)

    def test_decider_with_method(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add(_job('j1', 'b1', 'LLM', method='chat', received=t0))
            s.commit()

        result = _service(engine).get_batches()
        self.assertEqual(['LLM:chat x 1'], result.items[0].deciders)

    def test_multiple_deciders_in_one_batch(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'Whisper', received=t0),
                _job('j2', 'b1', 'Whisper', received=t0),
                _job('j3', 'b1', 'LLM', method='chat', received=t0),
            ])
            s.commit()

        result = _service(engine).get_batches()
        deciders = sorted(result.items[0].deciders)
        self.assertEqual(['LLM:chat x 1', 'Whisper x 2'], deciders)

    def test_deciders_not_mixed_across_batches(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        t1 = t0 + timedelta(hours=1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'Whisper', received=t0),
                _job('j2', 'b2', 'LLM', received=t1),
            ])
            s.commit()

        result = _service(engine).get_batches()
        by_id = {b.batch_id: b for b in result.items}
        self.assertEqual(['Whisper x 1'], by_id['b1'].deciders)
        self.assertEqual(['LLM x 1'], by_id['b2'].deciders)


class TestProgressAggregation(TestCase):
    """Progress formula: finished→1, in_work→job.progress (or 0), waiting→0; AVG over all jobs"""

    def test_all_finished(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'D', received=t0, accepted=t0, finished=t0 + timedelta(seconds=5), success=True),
                _job('j2', 'b1', 'D', received=t0, accepted=t0, finished=t0 + timedelta(seconds=5), success=True),
            ])
            s.commit()

        result = _service(engine).get_batches()
        self.assertAlmostEqual(1.0, result.items[0].progress)

    def test_none_started(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'D', received=t0),
                _job('j2', 'b1', 'D', received=t0),
            ])
            s.commit()

        result = _service(engine).get_batches()
        self.assertAlmostEqual(0.0, result.items[0].progress)

    def test_in_work_with_progress(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            # 1 finished (contributes 1.0), 1 in_work with progress=0.5 → avg = 0.75
            s.add_all([
                _job('j1', 'b1', 'D', received=t0, accepted=t0, finished=t0 + timedelta(seconds=1), success=True),
                _job('j2', 'b1', 'D', received=t0, accepted=t0, progress=0.5),
            ])
            s.commit()

        result = _service(engine).get_batches()
        self.assertAlmostEqual(0.75, result.items[0].progress, places=5)

    def test_in_work_without_progress_counts_as_zero(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            # 1 finished, 1 in_work with no progress → avg = (1.0 + 0.0) / 2 = 0.5
            s.add_all([
                _job('j1', 'b1', 'D', received=t0, accepted=t0, finished=t0 + timedelta(seconds=1), success=True),
                _job('j2', 'b1', 'D', received=t0, accepted=t0),
            ])
            s.commit()

        result = _service(engine).get_batches()
        self.assertAlmostEqual(0.5, result.items[0].progress, places=5)

    def test_waiting_counts_as_zero(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            # 1 finished, 1 waiting → avg = 0.5
            s.add_all([
                _job('j1', 'b1', 'D', received=t0, accepted=t0, finished=t0 + timedelta(seconds=1), success=True),
                _job('j2', 'b1', 'D', received=t0),
            ])
            s.commit()

        result = _service(engine).get_batches()
        self.assertAlmostEqual(0.5, result.items[0].progress, places=5)


class TestIsFinishedAndTimestamps(TestCase):
    """is_finished, finished_timestamp, total_processing_time"""

    def test_not_finished_when_job_waiting(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'D', received=t0, accepted=t0, finished=t0 + timedelta(seconds=5), success=True),
                _job('j2', 'b1', 'D', received=t0),
            ])
            s.commit()

        result = _service(engine).get_batches()
        b = result.items[0]
        self.assertFalse(b.is_finished)
        self.assertIsNone(b.finished_timestamp)
        self.assertIsNone(b.total_processing_time)

    def test_finished_when_all_done(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'D', received=t0, accepted=t0,
                     finished=t0 + timedelta(seconds=10), success=True),
                _job('j2', 'b1', 'D', received=t0, accepted=t0,
                     finished=t0 + timedelta(seconds=20), success=False),
            ])
            s.commit()

        result = _service(engine).get_batches()
        b = result.items[0]
        self.assertTrue(b.is_finished)
        self.assertEqual(t0 + timedelta(seconds=20), b.finished_timestamp)
        self.assertIsNotNone(b.total_processing_time)
        self.assertAlmostEqual(30.0, b.total_processing_time, places=1)

    def test_failure_counts_as_finished(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            s.add(_job('j1', 'b1', 'D', received=t0, accepted=t0,
                       finished=t0 + timedelta(seconds=5), success=False))
            s.commit()

        result = _service(engine).get_batches()
        b = result.items[0]
        self.assertTrue(b.is_finished)
        self.assertEqual(1, b.tasks_failure)
        self.assertEqual(0, b.tasks_success)


class TestPaginationAndOrdering(TestCase):
    """Batches are ordered newest-first; pagination via offset/size"""

    def _make_batches(self, engine):
        t0 = datetime(2024, 1, 1)
        with Session(engine) as s:
            for i in range(5):
                s.add(_job(f'j{i}', f'b{i}', 'D',
                           received=t0 + timedelta(hours=i)))
            s.commit()

    def test_newest_batch_first(self):
        engine = _engine()
        self._make_batches(engine)
        result = _service(engine).get_batches()
        ids = [b.batch_id for b in result.items]
        self.assertEqual('b4', ids[0])
        self.assertEqual('b0', ids[-1])

    def test_total_reflects_all_batches(self):
        engine = _engine()
        self._make_batches(engine)
        result = _service(engine).get_batches(offset=0, size=2)
        self.assertEqual(5, result.total)
        self.assertEqual(2, len(result.items))

    def test_offset_selects_correct_page(self):
        engine = _engine()
        self._make_batches(engine)
        page1 = _service(engine).get_batches(offset=0, size=2)
        page2 = _service(engine).get_batches(offset=2, size=2)
        self.assertNotEqual(page1.items[0].batch_id, page2.items[0].batch_id)
        self.assertEqual(5, page2.total)

    def test_empty_page_beyond_total(self):
        engine = _engine()
        self._make_batches(engine)
        result = _service(engine).get_batches(offset=10, size=5)
        self.assertEqual([], result.items)
        self.assertEqual(5, result.total)


class TestTrivialCounts(TestCase):
    """Task counts, received timestamp — all in one test"""

    def test_counts_and_received_timestamp(self):
        engine = _engine()
        t0 = datetime(2024, 1, 1, 10, 0, 0)
        t1 = t0 + timedelta(seconds=30)
        with Session(engine) as s:
            s.add_all([
                _job('j1', 'b1', 'D', received=t0),                                   # waiting
                _job('j2', 'b1', 'D', received=t0, accepted=t0),                      # in_work
                _job('j3', 'b1', 'D', received=t0, accepted=t0,
                     finished=t1, success=True),                                       # success
                _job('j4', 'b1', 'D', received=t0, accepted=t0,
                     finished=t1, success=False),                                      # failure
            ])
            s.commit()

        result = _service(engine).get_batches()
        b = result.items[0]
        self.assertEqual(4, b.tasks_total)
        self.assertEqual(1, b.tasks_waiting)
        self.assertEqual(1, b.tasks_in_work)
        self.assertEqual(1, b.tasks_success)
        self.assertEqual(1, b.tasks_failure)
        self.assertEqual(t0, b.received_timestamp)
