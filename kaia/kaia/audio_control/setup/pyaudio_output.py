import time

from kaia.infra import Loc, FileIO
import wave
from kaia.kaia.audio_control.core import IAudioOutput, AudioSample, AudioSampleTemplate
from io import BytesIO
from threading import Thread


class PlayInstance:
    def __init__(self, pyaudio, stream, wavfile, chunk=512):
        self.pyaudio = pyaudio
        self.stream = stream
        self.wavfile = wavfile
        self.chunk = chunk

    def run(self):
        data = self.wavfile.readframes(self.chunk)

        # play stream (looping from beginning of file to the end)
        while data:
            # writing to the stream is what *actually* plays the sound.
            self.stream.write(data)
            data = self.wavfile.readframes(self.chunk)

        # cleanup stuff.
        self.wavfile.close()
        self.stream.close()
        self.pyaudio.terminate()



class PyaudioOutput(IAudioOutput):
    def __init__(self):
        self.current_sample: AudioSample | None = None
        self.current_thread: Thread | None = None

    def start_playing(self, sample: AudioSample):
        import pyaudio

        self.current_sample = sample

        bts = BytesIO(sample.template.content)
        wf = wave.open(bts, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=
                        p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        play = PlayInstance(p, stream, wf)
        self.current_thread = Thread(target=play.run, daemon=True)
        self.current_thread.start()

    def what_is_playing(self) -> AudioSample|None:
        if self.current_thread is None:
            return None
        elif self.current_thread.is_alive():
            return self.current_sample
        else:
            self.current_thread = None
            self.current_sample = None
            return None

    def set_volume(self, volume: float):
        pass


if __name__ == '__main__':
    path = Loc.root_folder/'kaia/brainbox/deciders/docker_based/rhasspy/files/timer.wav'
    bytes = FileIO.read_bytes(path)
    data = AudioSampleTemplate(bytes).to_sample()
    output = PyaudioOutput()
    output.start_playing(data)
    while output.what_is_playing() is not None:
        time.sleep(0.1)