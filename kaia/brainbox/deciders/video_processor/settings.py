from dataclasses import dataclass


@dataclass
class VideoProcessorSettings:
    port: int = 11052
    startup_time_in_seconds: int = 60