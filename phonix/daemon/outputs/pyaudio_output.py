from .audio_output import IAudioOutput
import wave
from io import BytesIO
from threading import Thread


class PlayInstance:
    def __init__(self, pyaudio, stream, wavfile, chunk=512):
        self.pyaudio = pyaudio
        self.stream = stream
        self.wavfile = wavfile
        self.chunk = chunk
        self.terminate: bool = False

    def run(self):
        data = self.wavfile.readframes(self.chunk)

        # play stream (looping from beginning of file to the end)
        while data:
            # writing to the stream is what *actually* plays the sound.
            self.stream.write(data)
            data = self.wavfile.readframes(self.chunk)
            if self.terminate:
                break

        # cleanup stuff.
        self.wavfile.close()
        self.stream.close()
        self.pyaudio.terminate()


class PyAudioOutput(IAudioOutput):
    def __init__(self):
        self.current_thread: Thread | None = None
        self.current_instance: PlayInstance | None = None

    def start_playing(self, content: bytes):
        import pyaudio

        bts = BytesIO(content)
        wf = wave.open(bts, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=
                        p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        self.current_instance = PlayInstance(p, stream, wf)
        self.current_thread = Thread(target=self.current_instance.run, daemon=True)
        self.current_thread.start()

    def is_playing(self) -> bool:
        if self.current_thread is None:
            return False
        elif self.current_thread.is_alive():
            return True
        else:
            self.current_thread = None
            self.current_instance = None
            return False

    def cancel_playing(self):
        if self.current_instance is not None:
            self.current_instance.terminate = True
