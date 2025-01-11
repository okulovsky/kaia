from .audio_control_settings import AudioControlSettings
from ..wav_streaming import WavStreamingApi, WavApiSettings, WavStreamingRequest
from ..outputs import Recording, RecordingInstance
from queue import Queue
from .dto import MicState, IterationResult, AudioControlLog, LevelsLog
from datetime import datetime
from .mic_helper import MicDataHelper
from brainbox import BrainBoxTask
import traceback
import time


class AudioControlCycle:
    def __init__(self, settings: AudioControlSettings):
        self._settings = settings
        self._streaming_api = WavStreamingApi(WavApiSettings(
            self._settings.sample_rate,
            self._settings.frame_length,
            self._settings.wav_streaming_address
        ))
        self._requested_sounds = Queue()
        self._produced_files = Queue()
        self._drivers = settings.create_drivers()
        self._recording_playing: None|RecordingInstance = None
        self._mic_state = MicState.Standby
        self._streaming_request: None | WavStreamingRequest = None
        self._requested_state: None|MicState = None
        self._mic_helper = MicDataHelper(settings)
        self._levels: list[LevelsLog] = []
        self.last_update_time = datetime.now()
        self.responds_log: list[AudioControlLog] = []

    def request_recording(self, instance: RecordingInstance):
        self._requested_sounds.put(instance)

    def get_produced_file(self, block = False, timeout = None):
        return self._produced_files.get(block, timeout)

    def request_state(self, state: MicState):
        if state == MicState.Recording:
            raise ValueError("Cannot request RecordingState")
        self._requested_state = state


    def run(self):
        while True:
            now = datetime.now()

            try:
                result = self.iteration()

                if result.is_significant:
                    self.responds_log.append(AudioControlLog(now, result, None))
                self._levels.append(LevelsLog(now, result.level))
            except:
                ec = traceback.format_exc()
                self.responds_log.append(AudioControlLog(datetime.now(), None, ec))
                print(ec)


            if len(self.responds_log) > 2 * self._settings.max_log_entries:
                self.responds_log = self.responds_log[-self._settings.max_log_entries:]

            if len(self._levels) > 0 and (self._levels[0].timestamp - now).total_seconds() > 2*self._settings.max_levels_entries_in_seconds:
                self._levels = self._levels[len(self._levels)//2:]

            self.last_update_time = datetime.now()
            time.sleep(self._settings.pause_between_iterations_in_seconds)


    def iteration(self):
        if not self._drivers.input.is_running():
            self._drivers.input.start()

        data = self._drivers.input.read()
        sm = 0.0
        for s in data:
            sm += abs(float(s))
        level = sm / len(data)

        result = IterationResult(
            mic_state_before = self._mic_state,
            level = level,
            playing_before = self._recording_playing
        )

        busy_in_playing = self._process_recordings(result)
        result.playing_now = self._recording_playing

        if busy_in_playing:
            result.mic_state_now = self._mic_state
            return result

        self._process_mic_state()
        result.mic_state_now = self._mic_state

        if self._mic_state == MicState.Disabled:
            return result

        result.produced_file_name = self._process_mic(data, level)
        result.mic_state_now = self._mic_state
        return result

    def _process_recordings(self, result: IterationResult):
        currently_playing = self._drivers.output.what_is_playing()
        if currently_playing is not None:
            result.playing_now = currently_playing
            self._recording_playing = currently_playing
            return True

        if result.playing_before is not None:
            result.playing_before.state = RecordingInstance.State.Finished
            self._recording_playing = None
            return True

        if not self._requested_sounds.empty():
            playing: RecordingInstance = self._requested_sounds.get()
            playing.state = RecordingInstance.State.Playing
            self._drivers.output.start_playing(playing)
            self._recording_playing = playing
            if self._streaming_request is not None:
                self._streaming_request.cancel()
                self._streaming_request = None
            return True

        return False

    def _play_internal_recording(self, recording: Recording|None):
        if recording is None:
            return
        self._requested_sounds.put(RecordingInstance(recording, True))


    def _on_open(self):
        self._play_internal_recording(self._settings.open_recording)
        self._mic_helper.reset()
        self._mic_state = MicState.Open

    def get_state(self):
        return self._mic_state


    def _on_recording(self):
        filename = BrainBoxTask.safe_id()+".wav"
        self._streaming_request = self._drivers.streaming_api.create_request(filename, list(self._mic_helper.buffer))
        self._mic_state = MicState.Recording
        self._mic_helper.recording_started()

    def _on_recording_ended(self):
        fname = self._streaming_request.file_name
        self._streaming_request.send()
        self._produced_files.put(fname)
        self._streaming_request = None
        if self._settings.api_call_on_produced_file is not None:
            self._settings.api_call_on_produced_file(fname)
        self._mic_state = MicState.Standby
        self._play_internal_recording(self._settings.confirmed_recording)
        return fname

    def _process_mic_state(self):
        if self._requested_state is not None:
            self._mic_state = self._requested_state
            if self._mic_state == MicState.Open:
                self._on_open()
            self._requested_state = None
            return


    def _process_mic(self, data, level):
        if self._mic_state == MicState.Standby:
            if self._drivers.wakeword.detect(data):
                self._on_open()
            return

        is_silence = self._mic_helper.observe(data, level)

        if self._mic_state == MicState.Open:
            if not is_silence:
                self._on_recording()
            if self._settings.max_leading_length_in_seconds is not None:
                if self._mic_helper.silent_seconds > self._settings.max_leading_length_in_seconds:
                    self._mic_state = MicState.Standby
                    self._play_internal_recording(self._settings.error_recording)
            return

        if self._mic_state == MicState.Recording:
            if self._mic_helper.silent_seconds >= self._settings.silence_margin_in_seconds:
                return self._on_recording_ended()
            elif self._mic_helper.recorded_seconds > self._settings.max_length_in_seconds:
                return self._on_recording_ended()
            self._streaming_request.add_wav_data(data)
            return

        raise ValueError("Should not reach here")










