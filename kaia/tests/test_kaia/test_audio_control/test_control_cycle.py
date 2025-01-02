from typing import *
from unittest import TestCase
from pathlib import Path
from kaia.kaia.audio_control.audio_control_cycle import AudioControlCycle, MicState, IterationResult
from kaia.kaia.audio_control.inputs import FakeInput
from kaia.kaia import audio_control as ac

class Checker:
    def __init__(self, tc: TestCase, result: List[IterationResult]):
        self.tc = tc
        self.result = result
        self.index = 0

    def check(self,
              from_state: MicState,
              to_state: MicState,
              playing_before: str|None = None,
              playing_now: str|None = None,
              file_is_none: bool = True
              ):
        result = self.result[self.index]
        self.index+=1
        self.tc.assertEqual(from_state, result.mic_state_before)
        self.tc.assertEqual(to_state, result.mic_state_now)
        self.tc.assertEqual(playing_before is None, result.playing_before is None)
        if playing_before is not None:
            self.tc.assertEqual(playing_before.encode('utf-8'), result.playing_before.recording.content)
        self.tc.assertEqual(playing_now is None, result.playing_now is None)
        if playing_now is not None:
            self.tc.assertEqual(playing_now.encode('utf-8'), result.playing_now.recording.content)
        self.tc.assertEqual(file_is_none, result.produced_file_name is None)

    def print_current(self):
        for x in self.result[self.index:]:
            print(x)



class ControlCycleTestCase(TestCase):
    def _run(self, cc: AudioControlCycle, sample):
        mic: FakeInput = cc._drivers.input
        mic.set_sample(sample)
        result = []
        while not mic.is_buffer_empty():
            result.append(cc.iteration())
        return result


    def test_audio_control(self):
        settings = ac.AudioControlSettings(
            wav_streaming_address = None,
            mic_device_index=-1,
            sample_rate=22050,
            frame_length=512,
            silence_margin_in_seconds=0.1,
            pause_between_iterations_in_seconds=0.01,
            silence_level=1000,
            environment=ac.AudioControlSettings.Environments.Test,
        )

        settings.max_leading_length_in_seconds = settings.max_length_in_seconds

        cc = settings.create_audio_control()

        r1 = self._run(cc, Path(__file__).parent/'files/computer.wav')
        r2 = self._run(cc, Path(__file__).parent/'files/silence.wav')
        r3 = self._run(cc, Path(__file__).parent/'files/computer.wav')
        r4 = self._run(cc, Path(__file__).parent/'files/are_you_here.wav')
        cc.request_state(MicState.Open)
        r5 = self._run(cc,Path(__file__).parent/'files/make_me_a_sandwich.wav')

        result = r1+r2+r3+r4+r5
        result = [r for r in result if r.is_significant]
        c = Checker(self, result)

        s = MicState.Standby
        o = MicState.Open
        r = MicState.Recording

        # Computer
        c.check(s, o)
        c.check(o, o, playing_now='open')
        c.check(o, o, playing_before='open')

        # Silence
        c.check(o, s)
        c.check(s, s, playing_now='error')
        c.check(s, s, playing_before='error')

        # Computer
        c.check(s, o)
        c.check(o, o, playing_now='open')
        c.check(o, o, playing_before='open')

        # Are you here?
        c.check(o, r)
        c.check(r, s, file_is_none=False)
        c.check(s, s, playing_now='confirmed')
        c.check(s, s, playing_before='confirmed')


        #Manual state request
        c.check(s, o)
        c.check(o, o, playing_now='open')
        c.check(o, o, playing_before='open')
        c.check(o, r)
        c.check(r, s, file_is_none=False)
        c.check(s, s, playing_now='confirmed')
        c.check(s, s, playing_before='confirmed')

        self.assertEqual(c.index, len(c.result))
