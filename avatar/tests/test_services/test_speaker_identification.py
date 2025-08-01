from unittest import TestCase
from avatar.messaging import *
from avatar.services import SpeakerIdentificationService, BrainBoxService, State, SoundEvent
from yo_fluq import Query


class SpeakerIdentificationTestCase(TestCase):
    def test_speaker_identification(self):
        proc = AvatarProcessor(TestStream().create_client())
        state = State()
        proc.rules.bind(SpeakerIdentificationService(state,'test'))
        proc.rules.bind(BrainBoxService(SpeakerIdentificationService.brain_box_mock))

        proc.client.put(SoundEvent("test_speaker"))
        proc.debug_and_stop_by_empty_queue()
        self.assertEqual('test_speaker', state.user)

    def run_identification_retrain(self,
                                   target_speaker, speakers: list[str]
                                   ) -> tuple[BrainBoxService.Command, SpeakerIdentificationService.TrainConfirmation]:
        proc = AvatarProcessor(TestStream().create_client())
        state = State()
        proc.rules.bind(SpeakerIdentificationService(state,'test_model'))
        proc.rules.bind(BrainBoxService(SpeakerIdentificationService.brain_box_mock))

        for line in speakers:
            proc.client.put(SoundEvent(line))
        proc.debug_and_stop_by_empty_queue()
        proc.client.put(SpeakerIdentificationService.Train(target_speaker))
        result = proc.debug_and_stop_by_message_type(SpeakerIdentificationService.TrainConfirmation).messages
        confirmation = result[-1]
        bbox = Query.en(result).where(lambda z: isinstance(z, BrainBoxService.Command)).single_or_default()
        return bbox, confirmation

    def test_speaker_identification_retrain(self):
        bbox, confirmation = self.run_identification_retrain('test', ['test_1','test','test'])
        self.assertIsNone(bbox)
        self.assertFalse(confirmation.admit_errors)

    def test_one_retrain(self):
        bbox, confirmation = self.run_identification_retrain('test', ['test_1 1','test_1 2','test 3'])
        self.assertTrue(confirmation.admit_errors)
        prereqs = bbox.task.prerequisite.prereq
        self.assertEqual(1, len(prereqs))
        self.assertEqual(
            {'model': 'test_model', 'true_speaker': 'test', 'file': 'test_1 2'},
            prereqs[0].__dict__
        )

    def test_two_retrain(self):
        bbox, confirmation = self.run_identification_retrain('test', ['test_1 1', 'test_1 2', 'test_1 3'])
        self.assertTrue(confirmation.admit_errors)
        prereqs = bbox.task.prerequisite.prereq
        self.assertEqual(2, len(prereqs))
        self.assertEqual(
            {'model': 'test_model', 'true_speaker': 'test', 'file': 'test_1 2'},
            prereqs[0].__dict__
        )
        self.assertEqual(
            {'model': 'test_model', 'true_speaker': 'test', 'file': 'test_1 3'},
            prereqs[1].__dict__
        )



