from dataclasses import dataclass

@dataclass
class AudioPlayConfirmation:
    id: str

@dataclass
class AudioCommand:
    id: str

class InitializationCommand:
    pass

class TimerTick:
    pass
