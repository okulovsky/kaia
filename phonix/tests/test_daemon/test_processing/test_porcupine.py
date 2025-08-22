from phonix.daemon.processing import PorcupineWakeWordUnit, UnitInput, MicState, State, SystemSoundCommand, SystemSoundType, IMonitor
from phonix.daemon.inputs import FakeInput
from avatar.messaging import TestStream
from avatar.daemon import WakeWordEvent
from unittest import TestCase
from pathlib import Path
from yo_fluq import Query, FileIO
from foundation_kaia.misc import Loc

def check(file):
    if isinstance(file, str):
        file = Path(__file__).parent.parent.parent / 'files' / file
    input = FakeInput()
    input.set_sample(FileIO.read_bytes(file))
    porcupine = PorcupineWakeWordUnit()
    client = TestStream().create_client(None)
    clone_client = client.clone()
    result = []
    while not input.is_buffer_empty():
        data = input.read()
        result.append(porcupine.process(UnitInput(
            State(MicState.Standby),
            data,
            (),
            False,
            IMonitor(),
            client.put
        )))
    return result, clone_client.pull()


class PorcupineTestCase(TestCase):
    def test_porcupine_positive(self):
        states, messages = check('computer.wav')
        not_null = Query.en(states).where(lambda z: z is not None).single()
        self.assertEqual(MicState.Opening, not_null.mic_state)
        self.assertEqual(2, len(messages))
        self.assertIsInstance(messages[0], WakeWordEvent)
        self.assertEqual('computer', messages[0].word)
        self.assertIsInstance(messages[1], SystemSoundCommand)
        self.assertEqual(SystemSoundType.opening, messages[1].sound)

    def test_porcupine_negative(self):
        states, messages = check('sandwich.wav')
        self.assertEqual({None}, set(states))
        self.assertEqual(0, len(messages))






