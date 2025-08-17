import sys
import subprocess

class LinuxVolume:
    def set(self, level: float) -> None:
        lvl = 0.0 if level < 0 else 1.0 if level > 1 else float(level)
        pct = str(int(round(lvl * 100)))
        subprocess.check_call(['amixer', '-D', 'pulse', 'sset', 'Master', f'{pct}%'])


class MacVolume:
    def set(self, level: float) -> None:
        lvl = 0.0 if level < 0 else 1.0 if level > 1 else float(level)
        pct = int(round(lvl * 100))
        subprocess.check_call(['osascript', '-e', f'set volume output volume {pct}'])


class WindowsVolume:
    def __init__(self):
        # Ленивые импорты и привязка к устройству
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self._volume = cast(interface, POINTER(IAudioEndpointVolume))

    def set(self, level: float) -> None:
        lvl = 0.0 if level < 0 else 1.0 if level > 1 else float(level)
        self._volume.SetMasterVolumeLevelScalar(lvl, None)

class VolumeController:
    def __init__(self):
        if sys.platform.startswith("linux"):
            self._impl = LinuxVolume()
        elif sys.platform == "darwin":
            self._impl = MacVolume()
        elif sys.platform.startswith("win"):
            self._impl = WindowsVolume()
        else:
            raise NotImplementedError(sys.platform)

    def set(self, level: float) -> None:
        self._impl.set(level)
