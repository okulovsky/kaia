import time
import traceback
from queue import Queue
from .dto import *
from .audio_control_debug_console import IAudioControlDebugConsole, AudioControlDebugItem
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AudioControlData:
    source: str
    payload: Any


@dataclass
class AudioControlLog:
    timestamp: datetime
    iteration_result: IterationResult| None
    exception: str| None


class AudioControl:
    def __init__(self,
                 input: IAudioInput,
                 output: IAudioOutput,
                 default_pipeline: IPipeline,
                 pipelines: Iterable[IPipeline],
                 audio_samples: dict[str, AudioSampleTemplate],
                 pause_between_iterations_in_seconds: float,
                 audio_control_debug_console: None | IAudioControlDebugConsole = None
                 ):
        self.input = input
        self.output = output
        self.pause_between_iterations_in_seconds = pause_between_iterations_in_seconds

        self.default_pipeline = default_pipeline
        self.pipelines = {p.get_name(): p for p in pipelines}
        self.audio_samples = audio_samples

        self.current_pipeline = self.default_pipeline
        self.was_playing: None | AudioSample = None

        self.play_requests_queue: Queue = Queue()
        self.states_requests_queue: Queue = Queue()
        self.commands_queue: Queue = Queue()
        self.paused = False
        self.audio_control_debug_console = audio_control_debug_console
        self.last_update_time: datetime = datetime.now()
        self.responds_log: list[AudioControlLog] = []
        self.responds_log_length = 20

    def set_pipeline(self, mode: str):
        self.states_requests_queue.put(mode)


    def run(self):
        while True:
            if not self.paused:
                try:
                    result = self.iteration()
                    if not result.is_empty():
                        self.responds_log.append(AudioControlLog(datetime.now(), result, None))
                except:
                    ec = traceback.format_exc()
                    self.responds_log.append(AudioControlLog(datetime.now(), None, ec))
                    print(ec)


                if len(self.responds_log) > 2 * self.responds_log_length:
                    self.responds_log = self.responds_log[-self.responds_log_length:]

            self.last_update_time = datetime.now()
            time.sleep(self.pause_between_iterations_in_seconds)


    def set_paused(self, pause: bool):
        if pause:
            self.input.stop()
            self.paused = True
        else:
            self.input.start()
            self.paused = False



    def iteration(self) -> IterationResult:
        state_before = self.current_pipeline.get_name()
        is_playing = self.output.what_is_playing()

        data = None
        pipeline_state = None
        to_return = None

        if is_playing is not None:
            self.was_playing = is_playing
            to_return = IterationResult(state_before, self.current_pipeline.get_name(), self.was_playing, None, None, None)

        elif self.was_playing is not None:
            was_playing = self.was_playing
            self.was_playing = None
            was_playing.state = AudioSample.State.Finished
            if not was_playing.internal:
                self.current_pipeline = self.default_pipeline
                self.current_pipeline.reset()
            to_return = IterationResult(state_before, self.current_pipeline.get_name(), None, None, was_playing, None)

        elif not self.play_requests_queue.empty():
            if self.input.is_running():
                self.input.stop()
            playing: AudioSample = self.play_requests_queue.get()
            playing.state = AudioSample.State.Playing
            self.output.start_playing(playing)
            self.was_playing = playing
            to_return = IterationResult(state_before, self.current_pipeline.get_name(), playing, playing, None, None)

        elif not self.states_requests_queue.empty():
            requested_state = self.states_requests_queue.get()
            while not self.states_requests_queue.empty():
                requested_state = self.states_requests_queue.get()
            self.current_pipeline: IPipeline = self.pipelines[requested_state]
            self.current_pipeline.reset()
            confirmation = self.current_pipeline.get_entering_sound_key()
            if confirmation is not None:
                if isinstance(confirmation, str):
                    confirmation = self.audio_samples[confirmation]
                self.play_requests_queue.put(AudioSample(confirmation, True))
            to_return = IterationResult(state_before, self.current_pipeline.get_name(), None, None, None, None)

        else: #if we're here, audio is not playing, not just finished playing, not requested, and the state change is not requested.
            if not self.input.is_running():
                self.input.start()

            data = self.input.read()
            result = self.current_pipeline.process(data)
            if self.audio_control_debug_console is not None:
                pipeline_state = self.current_pipeline.get_state()

            if result is None:
                to_return = IterationResult(state_before, self.current_pipeline.get_name(), None, None, None, None)
            else:
                if result.play_sound is not None:
                    if self.play_requests_queue.empty():
                        sample = AudioSample(self.audio_samples[result.play_sound],True)
                        self.play_requests_queue.put(sample)
                if result.next_state is not None:
                    self.current_pipeline = self.pipelines[result.next_state]
                else:
                    self.current_pipeline = self.default_pipeline
                if result.collected_data is not None:
                    self.commands_queue.put(AudioControlData(state_before, result.collected_data))
                self.current_pipeline.reset()
                to_return = IterationResult(state_before, self.current_pipeline.get_name(), None, None, None, result)


        if self.audio_control_debug_console is not None:
            debug_item = AudioControlDebugItem(
                is_playing,
                self.input.is_running(),
                data,
                state_before,
                pipeline_state
            )
            self.audio_control_debug_console.observe(debug_item)

        return to_return

