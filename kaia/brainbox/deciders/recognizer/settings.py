from dataclasses import dataclass


@dataclass
class RecognizerSettings:
    port: int = 11029
    startup_time_in_seconds: int = 60