from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AudioPlayConfirmation:
    id: str

@dataclass
class AudioCommand:
    id: str

class InitializationCommand:
    pass

@dataclass
class TimerTick:
    current_time: datetime = field(default_factory=datetime.now)

