from dataclasses import dataclass

@dataclass(frozen=True)
class ConnectionSettings:
    port: int
    loading_time_in_seconds: int = 10