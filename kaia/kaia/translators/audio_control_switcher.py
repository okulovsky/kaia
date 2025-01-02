from eaglesong.core import Translator, Listen
from kaia.kaia.audio_control import AudioControlApi, MicState
from kaia.kaia.translators import OpenMic
from brainbox import File


class AudioControlSwitcherTranslator(Translator):
    def __init__(self,
                 inner_function,
                 api: AudioControlApi,

                 ):
        self.api = api
        self.sounds_to_play = set()
        self.target_state: None|MicState = None
        super().__init__(inner_function,
                         input_function_translator=self._translate_input,
                         output_function_translator=self._translate_output
                         )

    def reduce_and_send_if_empty(self, name: str|None):
        if name in self.sounds_to_play:
            self.sounds_to_play.remove(name)
            if len(self.sounds_to_play) == 0:
                target_state = self.target_state
                if target_state is None:
                    target_state = MicState.Standby
                self.api.set_state(target_state)
                self.target_state = None

    def _translate_input(self, input:Translator.InputPackage):
        from ..driver import AudioPlayConfirmation
        if not isinstance(input.outer_input, AudioPlayConfirmation):
            return input.outer_input
        else:
            self.reduce_and_send_if_empty(input.outer_input.id)
            return Translator.NoInput

    def _translate_output(self, output: Translator.OutputPackage):
        if isinstance(output.inner_output, File) and output.inner_output.kind == File.Kind.Audio:
            if len(self.sounds_to_play) == 0:
                current_state = self.api.get_state()
                if current_state == MicState.Recording:
                    current_state = MicState.Standby
                self.api.set_state(MicState.Disabled)
                self.target_state = current_state

            self.sounds_to_play.add(output.inner_output.name)
            return output.inner_output
        if isinstance(output.inner_output, Listen):
            if OpenMic in output.inner_output:
                open_mic = output.inner_output[OpenMic]
                target_state = MicState.Standby if not open_mic.open_mic else MicState.Open
                if len(self.sounds_to_play) == 0:
                    self.api.set_state(target_state)
                else:
                    self.target_state = target_state
            return output.inner_output
        return output.inner_output









