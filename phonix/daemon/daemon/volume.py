import sys
import subprocess


class LinuxVolume:
    def set(self, level: float) -> None:
        lvl = 0.0 if level < 0 else 1.0 if level > 1 else float(level)
        pct = str(int(round(lvl * 100)))
        subprocess.check_call(["amixer", "-D", "pulse", "sset", "Master", f"{pct}%"])

    def get(self) -> float:
        # amixer sget Master → ищем строку "Front Left:" или "Mono:" с "[XX%]"
        out = subprocess.check_output(
            ["amixer", "-D", "pulse", "sget", "Master"], text=True
        )
        for line in out.splitlines():
            if "%" in line:
                # Пример: "  Front Left: Playback 50 [74%] ..."
                start = line.find("[")
                end = line.find("%", start)
                if start != -1 and end != -1:
                    pct = int(line[start+1:end])
                    return pct / 100.0
        return 0.0


class MacVolume:
    def set(self, level: float) -> None:
        lvl = 0.0 if level < 0 else 1.0 if level > 1 else float(level)
        pct = int(round(lvl * 100))
        subprocess.check_call(
            ["osascript", "-e", f"set volume output volume {pct}"]
        )

    def get(self) -> float:
        # osascript -e "output volume of (get volume settings)"
        out = subprocess.check_output(
            ["osascript", "-e", "output volume of (get volume settings)"],
            text=True
        )
        pct = int(out.strip())
        return pct / 100.0


class WindowsVolume:
    def __init__(self):
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self._volume = cast(interface, POINTER(IAudioEndpointVolume))

    def set(self, level: float) -> None:
        lvl = 0.0 if level < 0 else 1.0 if level > 1 else float(level)
        self._volume.SetMasterVolumeLevelScalar(lvl, None)

    def get(self) -> float:
        # Возвращает float от 0.0 до 1.0
        return float(self._volume.GetMasterVolumeLevelScalar())


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

    def get(self) -> float:
        return self._impl.get()
