from unittest import TestCase
from sqlalchemy import create_engine
from brainbox.framework.job_processing.core.job import BrainBoxBase
from brainbox.framework.job_processing.main_loop import CancelAction, CommandQueue
from brainbox.framework.app.batches import BatchesService


class TestCancelBatch(TestCase):
    def test_cancel_enqueues_cancel_action_with_correct_batch_id(self):
        engine = create_engine('sqlite://')
        BrainBoxBase.metadata.create_all(engine)
        queue = CommandQueue()
        service = BatchesService(engine, queue)

        service.cancel_batch('my-batch-123')

        self.assertEqual(1, queue.qsize())
        action = queue.get_nowait()
        self.assertIsInstance(action, CancelAction)
        self.assertEqual('my-batch-123', action.cancel_batch_id)
        self.assertIsNone(action.cancel_job_id)
