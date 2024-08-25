from dataclasses import dataclass

@dataclass
class ResemblyzerSettings:
    port: int = 11006
    startup_time_in_seconds: int = 15
