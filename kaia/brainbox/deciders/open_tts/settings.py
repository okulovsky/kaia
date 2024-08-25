from dataclasses import dataclass

@dataclass
class OpenTTSSettings:
    port: int = 11002
    startup_time_in_seconds: int = 30