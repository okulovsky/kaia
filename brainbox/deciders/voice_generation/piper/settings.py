from dataclasses import dataclass

@dataclass
class PiperSettings:
    port: int = 11007
    startup_time_in_seconds: int = 15