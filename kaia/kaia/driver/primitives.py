from dataclasses import dataclass

@dataclass
class AudioPlayConfirmation:
    id: str

@dataclass
class AudioCommand:
    id: str

class Start:
    pass

class TimerTick:
    pass


@dataclass
class Start:
    first_time: bool



