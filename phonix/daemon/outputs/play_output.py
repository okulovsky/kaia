import os
import tempfile
import subprocess
from threading import Lock
from .audio_output import IAudioOutput

class SoxAudioOutput(IAudioOutput):
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._tmpfile: str | None = None
        self._lock = Lock()

    def start_playing(self, content: bytes):
        if self._proc is not None and self._proc.poll() is None:
            self._proc.kill()
        if self._tmpfile and os.path.exists(self._tmpfile):
            try: os.remove(self._tmpfile)
            except OSError: pass
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with open(path, "wb") as f:
                f.write(content)
            self._tmpfile = path
            self._proc = subprocess.Popen(
                ["play", "-q", self._tmpfile],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def is_playing(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def cancel_playing(self):
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
        if self._tmpfile and os.path.exists(self._tmpfile):
            try: os.remove(self._tmpfile)
            except OSError: pass
        self._tmpfile = None