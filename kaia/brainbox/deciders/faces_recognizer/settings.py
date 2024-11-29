from dataclasses import dataclass


@dataclass
class FacesRecognizerSettings:
    port: int = 11029
    startup_time_in_seconds: int = 60