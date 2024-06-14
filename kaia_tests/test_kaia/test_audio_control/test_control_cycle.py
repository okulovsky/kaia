from typing import *
from unittest import TestCase
from kaia.avatar.dub.core import Utterance
from kaia.infra import FileIO
from kaia_tests.test_kaia.test_audio_control.audio_control_cycle import create_audio_control_settings, get_intents
from pathlib import Path
from kaia.kaia.audio_control import core as ac
from yo_fluq import *


class Checker:
    def __init__(self, tc: TestCase, result):
        self.tc = tc
        self.result = result
        self.index = 0

    def check(self,
              from_state: str,
              to_state: str,
              started_content: str|None = None,
              finished_content: str|None = None,
              input_result_checker: Optional[Callable] = None
              ):
        result = self.result[self.index]
        self.index+=1
        self.tc.assertEqual(from_state, result.from_state)
        self.tc.assertEqual(to_state, result.to_state)
        self.tc.assertEqual(started_content is None, result.audio_sample_playing is None)
        if started_content is not None:
            self.tc.assertEqual(started_content.encode('utf-8'), result.audio_sample_started.template.content)
        self.tc.assertEqual(finished_content is None, result.audio_sample_finished is None)
        if finished_content is not None:
            self.tc.assertEqual(finished_content.encode('utf-8'), result.audio_sample_finished.template.content)
        self.tc.assertEqual(input_result_checker is None, result.processed_input is None)
        if input_result_checker is not None:
            self.tc.assertTrue(input_result_checker(result.processed_input))



class ControlCycleTestCase(TestCase):
    def _run(self, cc: ac.AudioControl):
        mic: ac.FakeInput = cc.input
        mic.next_buffer()
        result = []
        while not mic.is_buffer_empty():
            result.append(cc.iteration())
        return result


    def test_audio_control(self):
        settings = create_audio_control_settings()
        settings.max_leading_length_in_seconds = settings.max_length_in_seconds
        settings.load_mic_samples = [
            Path(__file__).parent/'files/computer.wav',
            Path(__file__).parent/'files/silence.wav',
            Path(__file__).parent/'files/computer.wav',
            Path(__file__).parent/'files/are_you_here.wav',
            Path(__file__).parent/'files/random_text_outside_of_intents.wav',

        ]
        settings.rhasspy_api.setup_intents(get_intents())
        settings.rhasspy_api.train()
        cc = settings.create_audio_control()


        r1 = self._run(cc)
        r2 = self._run(cc)
        r3 = self._run(cc)
        r4 = self._run(cc)
        cc.set_pipeline('whisper')
        r5 = self._run(cc)
        result = r1 + r2 + r3 + r4 + r5
        result = [r for r in result if not r.is_empty()]
        for r in result:
            print(r)

        p='porcupine'
        r='rhasspy'
        w='whisper'

        c = Checker(self, result)

        #Computer
        c.check(p, r, input_result_checker=lambda z: z is not None and z.collected_data is None)
        c.check(r, r, started_content='awake')
        c.check(r, r, finished_content='awake')

        #Silence
        c.check(r, p, input_result_checker=lambda z: z is not None and z.play_sound=='error')
        c.check(p, p, started_content='error')
        c.check(p, p, finished_content='error')

        #Computer
        c.check(p, r, input_result_checker=lambda z: z is not None and z.collected_data is None)
        c.check(r, r, started_content='awake')
        c.check(r, r, finished_content='awake')

        #Are you here?
        c.check(r, p, input_result_checker=lambda z: isinstance(z.collected_data, dict))
        c.check(p, p, started_content='confirmed')
        c.check(p, p, finished_content='confirmed')

        #External text
        c.check(w, w, started_content='open')
        c.check(w, w, finished_content='open')
        c.check(w, p, input_result_checker=lambda z: isinstance(z.collected_data, str))
        c.check(p, p, started_content='confirmed')
        c.check(p, p, finished_content='confirmed')




